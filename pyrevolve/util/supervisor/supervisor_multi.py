from __future__ import absolute_import
from __future__ import print_function

import atexit
import subprocess
import os
import psutil
import sys
import asyncio

from datetime import datetime

from ...custom_logging.logger import create_logger

from .nbsr import NonBlockingStreamReader as NBSR

mswindows = (sys.platform == "win32")


def terminate_process(proc):
    """
    Recursively kills a process and all of its children
    :param proc: Result of `subprocess.Popen`

    Inspired by http://stackoverflow.com/a/25134985/358873

    TODO Check if terminate fails and kill instead?
    :return:
    """
    process = psutil.Process(proc.pid)
    for child in process.children(recursive=True):
        child.terminate()

    process.terminate()


class DynamicSimSupervisor(object):
    """
    Utility class that allows you to automatically restore a crashing
    experiment and continue to run it from a snapshotted. It does so
    by assuming a snapshot functionality similar to that in Revolve.Angle's
    WorldManager. The supervisor launches subprocesses for (a) a world
    and (b) your manager / experiment. It determines a fixed output directory
    for this experiment run, which is provided to the manager with
    the `restore_arg` argument.

    The experiment is considered finished if any of the processes exit with 0
    code. If any of processes exit with non zero code, the experiment dies.
    """

    def __init__(self,
                 world_file,
                 output_directory=None,
                 simulator_cmd="gzserver",
                 simulator_args=None,
                 restore_arg="--restore-directory",
                 snapshot_world_file="snapshot.world",
                 restore_directory=None,
                 plugins_dir_path=None,
                 models_dir_path=None,
                 simulator_name='simulator'
                 ):
        """

        :param world_file: Full path (or relative to cwd) to the Gazebo world
                           file to load.
        :param output_directory: Full path (or relative to cwd) to the output
                                 directory, which will be the parent of the
                                 restore directory.
        :param simulator_cmd: Command to runs the Simulator
        :param simulator_args: Arguments to the Simulator, *excluding* the world file name
        :param restore_arg: Argument used to pass the snapshot/restore
                            directory name to the manager. Note that the
                            output directory is not passed as part of this
                            name, just the relative path.
        :param snapshot_world_file:
        :param restore_directory:
        :param plugins_dir_path: Full path (or relative to cwd) to the simulator
                                 plugins directory (setting env variable
                                 GAZEBO_PLUGIN_PATH).
        :param models_dir_path: Full path (or relative to cwd) to the simulator
                                models directory (setting env variable
                                GAZEBO_MODEL_PATH).
        """
        self.restore_directory = datetime.now().strftime('%Y%m%d%H%M%S') \
            if restore_directory is None else restore_directory
        self.output_directory = 'output' \
            if output_directory is None else os.path.abspath(output_directory)
        self.snapshot_directory = os.path.join(
            self.output_directory,
            self.restore_directory)
        self.snapshot_world_file = snapshot_world_file
        self.restore_arg = restore_arg
        self.simulator_args = simulator_args if simulator_args is not None else ["-u"]
        self.simulator_cmd = simulator_cmd \
            if isinstance(simulator_cmd, list) else [simulator_cmd]
        self._simulator_name = simulator_name

        self.world_file = os.path.abspath(world_file)

        self.streams = {}
        self.procs = {}
        self.stream_future = None
        self._logger = create_logger(simulator_name)

        # Terminate all processes when the supervisor exits
        atexit.register(self._terminate_all)

        # Set plugins dir path for Gazebo
        if plugins_dir_path is not None:
            plugins_dir_path = os.path.abspath(plugins_dir_path)
            try:
                new_env_var = "{curr_paths}:{new_path}".format(
                    curr_paths=os.environ["GAZEBO_PLUGIN_PATH"],
                    new_path=plugins_dir_path)
            except KeyError:
                new_env_var = plugins_dir_path
            os.environ["GAZEBO_PLUGIN_PATH"] = new_env_var

        # Set models dir path for Gazebo
        if models_dir_path is not None:
            models_dir_path = os.path.abspath(models_dir_path)
            try:
                new_env_var = "{curr_paths}:{new_path}".format(
                    curr_paths=os.environ["GAZEBO_MODEL_PATH"],
                    new_path=models_dir_path)
            except KeyError:
                new_env_var = models_dir_path
            os.environ['GAZEBO_MODEL_PATH'] = new_env_var

        self._logger.info("Created Supervisor with:"
                          "\n\t- simulator command: {} {}"
                          "\n\t- world file: {}"
                          "\n\t- simulator plugin dir: {}"
                          "\n\t- simulator models dir: {}"
                          .format(simulator_cmd,
                                  simulator_args,
                                  world_file,
                                  plugins_dir_path,
                                  models_dir_path)
                          )

    def launch_simulator(self, address='localhost', port=11345):
        f = self._launch_simulator(output_tag=self._simulator_name, address=address, port=port)

        def start_output_listening(_future):
            self.stream_future = asyncio.ensure_future(self._poll_simulator())

        f.add_done_callback(start_output_listening)
        return f

    async def relaunch(self, sleep_time=1):
        self.stop()
        await asyncio.sleep(sleep_time)
        return self.launch_simulator()

    def stop(self):
        if self.stream_future is not None:
            self.stream_future.cancel()
        self._terminate_all()

    async def _poll_simulator(self, sleep_interval=0.1):
        self._pass_through_stdout()
        for proc_name in self.procs:
            ret = self.procs[proc_name].poll()
            if ret is not None:
                if ret == 0:
                    self._logger.info("Program {} exited normally"
                                      .format(proc_name))
                else:
                    self._logger.error("Program {} exited with code {}"
                                       .format(proc_name, ret))

                return ret
        await asyncio.sleep(sleep_interval)
        self._task = asyncio.ensure_future(self._poll_simulator(sleep_interval))

    def _pass_through_stdout(self):
        """
        Passes process piped standard out through to normal stdout
        :return:
        """
        for NBSRout, NBSRerr in list(self.streams.values()):
            try:
                for _ in range(1000):
                    out = NBSRout.readline(0.005)
                    err = NBSRerr.readline(0.005)

                    if not out and not err:
                        break

                    if out:
                        self.write_stdout(out)

                    if err:
                        self.write_stderr(err)
            except Exception as e:
                self._logger.exception("Exception while handling file reading")

    def write_stdout(self, data):
        """
        Overridable method to write to stdout, useful if you
        want to apply some kind of filter, or write to a file
        instead.
        :param self:
        :param data:
        :return:
        """
        data = str(data).strip()
        if len(data) > 0:
            self._logger.info(data)
        # sys.stdout.write(data)

    def write_stderr(self, data):
        """
        Overridable method to write to stderr, useful if you
        want to apply some kind of filter, or write to a file
        instead.
        :param data:
        :return:
        """
        data = str(data).strip()
        if len(data) > 0:
            self._logger.error(data)
        # sys.stderr.write(data)

    def _terminate_all(self):
        """
        Terminates all running processes
        :return:
        """
        self._logger.info("Terminating processes...")
        for proc in list(self.procs.values()):
            if proc.poll() is None:
                terminate_process(proc)

        # flush output of all processes
        # TODO: fix this better
        self._pass_through_stdout()

        self.procs = {}

    def _add_output_stream(self, name):
        """
        Creates a non blocking stream reader for the process with
        the given name, and adds it to the streams that are passed
        through.
        :param name:
        :return:
        """
        # self.streams[name] = (NBSR(self.procs[name].stdout, name),
        #                       NBSR(self.procs[name].stderr, name))
        self.streams[name] = (NBSR(self.procs[name].stdout, prefix=None),
                              NBSR(self.procs[name].stderr, prefix=None))

    def _launch_simulator(self, ready_str="World plugin loaded", output_tag="simulator", address='localhost',
                          port=11345):
        """
        Launches the simulator
        :return:
        """

        async def start_process(_ready_str, _output_tag, _address, _port):
            self._logger.info("Launching the simulator...")
            gz_args = self.simulator_cmd + self.simulator_args
            snapshot_world = os.path.join(
                self.snapshot_directory,
                self.snapshot_world_file)
            world = snapshot_world \
                if os.path.exists(snapshot_world) else self.world_file
            gz_args.append(world)

            env = {}
            for key, value in os.environ.items():
                env[key] = value
            env['GAZEBO_MASTER_URI'] = 'http://{}:{}'.format(_address, _port)
            self.procs[_output_tag] = await self._launch_with_ready_str(
                cmd=gz_args,
                ready_str=_ready_str,
                env=env,
                output_tag=_output_tag)
            self._add_output_stream(_output_tag)

        simulator_started = asyncio.ensure_future(start_process(ready_str, output_tag, address, port))
        return simulator_started

    async def _launch_with_ready_str(self, cmd, ready_str, env, output_tag="simulator"):
        """
        :param cmd:
        :param ready_str:
        :return:
        """
        process = subprocess.Popen(
            cmd,
            bufsize=1,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        # make out and err non-blocking pipes
        if not mswindows:
            import fcntl
            for pipe in [process.stdout, process.stderr]:
                fd = pipe.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        else:
            # hint on how to fix it here:
            # https://github.com/cs01/gdbgui/issues/18#issuecomment-284263708
            self._logger.error("Windows may not give the optimal experience")

        ready = False
        await asyncio.sleep(0.1)
        while not ready:
            exit_code = process.poll()
            if exit_code is not None:
                # flush out all stdout and stderr
                out, err = process.communicate()
                if out is not None:
                    self._logger.info("{}".format(out.decode('utf-8')))
                if err is not None:
                    self._logger.error("{}".format(err.decode('utf-8')))
                raise RuntimeError("Error launching {}, exit with code {}"
                                   .format(cmd, exit_code))

            try:
                out = process.stdout.readline().decode('utf-8')
                if len(out) > 0:
                    self._logger.info("[launch] {}".format(out.strip()))
                if ready_str in out:
                    ready = True
            except IOError:
                pass

            if not mswindows:
                try:
                    err = process.stderr.readline().decode('utf-8')
                    if len(err) > 0:
                        self._logger.error("[launch] {}".format(err.strip()))
                except IOError:
                    pass

            await asyncio.sleep(0.2)
        # make out and err blocking pipes again
        if not mswindows:
            import fcntl
            for pipe in [process.stdout, process.stderr]:
                fd = pipe.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl & (~ os.O_NONBLOCK))
        else:
            # hint on how to fix it here:
            # https://github.com/cs01/gdbgui/issues/18#issuecomment-284263708
            self._logger.error("Windows may not give the optimal experience")

        return process
