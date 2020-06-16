from __future__ import absolute_import
from __future__ import print_function

import atexit
import subprocess
import os
import psutil
import sys
import time

from datetime import datetime

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


class Supervisor(object):
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
                 manager_cmd,
                 world_file,
                 output_directory=None,
                 manager_args=None,
                 simulator_cmd="gzserver",
                 simulator_args=None,
                 restore_arg="--restore-directory",
                 snapshot_world_file="snapshot.world",
                 restore_directory=None,
                 plugins_dir_path=None,
                 models_dir_path=None
                 ):
        """

        :param manager_cmd: The command used to run your manager / experiment
        :param world_file: Full path (or relative to cwd) to the Gazebo world
                           file to load.
        :param output_directory: Full path (or relative to cwd) to the output
                                 directory, which will be the parent of the
                                 restore directory.
        :param manager_args: Commands to pass to the manager
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
        self.manager_args = manager_args if manager_args is not None else []
        self.manager_args += [self.restore_arg, self.snapshot_directory]

        self.world_file = os.path.abspath(world_file)
        self.manager_cmd = manager_cmd \
            if isinstance(manager_cmd, list) else [manager_cmd]

        self.streams = {}
        self.procs = {}

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
                        curr_paths=os.environ["GAZEBO_MODEL_PATHm"],
                        new_path=models_dir_path)
            except KeyError:
                new_env_var = models_dir_path
            os.environ['GAZEBO_MODEL_PATH'] = new_env_var

        print("Created Supervisor with:"
              "\n\t- manager command: {} {}"
              "\n\t- simulator command: {} {}"
              "\n\t- world file: {}"
              "\n\t- simulator plugin dir: {}"
              "\n\t- simulator models dir: {}"
              .format(manager_cmd,
                      manager_args,
                      simulator_cmd,
                      simulator_args,
                      world_file,
                      plugins_dir_path,
                      models_dir_path)
              )

    def launch_simulator(self):
        print("\nNOTE: launching only a simulator, not a manager script!\n")
        self._launch_simulator()

        # Wait for the end
        while True:
            for proc_name in self.procs:
                self._pass_through_stdout()
                ret = self.procs[proc_name].poll()
                if ret is not None:
                    if ret == 0:
                        sys.stdout.write("Program {} exited normally\n"
                                         .format(proc_name))
                    else:
                        sys.stderr.write("Program {} exited with code {}\n"
                                         .format(proc_name, ret))

                    return ret

    def launch(self):
        """
        (Re)launches the experiment.
        :return:
        """
        # if not os.path.exists(self.output_directory):
        #     os.mkdir(self.output_directory)
        # if not os.path.exists(self.snapshot_directory):
        #     os.mkdir(self.snapshot_directory)

        print("Launching all processes...")
        self._launch_simulator()
        self._launch_manager()

        while True:
            for proc_name in self.procs:
                # Write out all received stdout
                self._pass_through_stdout()

                ret = self.procs[proc_name].poll()
                if ret is not None:
                    if ret == 0:
                        sys.stdout.write("Program '{}' exited normally\n"
                                         .format(proc_name))
                    else:
                        sys.stderr.write("Program '{}' exited with code {}\n"
                                         .format(proc_name, ret))

                    return ret

            # We could do this a lot less often, but this way we get
            # output once every second.
            time.sleep(0.1)

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
                print("Exception while handling file reading:\n{}".format(e), file=sys.stderr)

    @staticmethod
    def write_stdout(data):
        """
        Overridable method to write to stdout, useful if you
        want to apply some kind of filter, or write to a file
        instead.
        :param self:
        :param data:
        :return:
        """
        sys.stdout.write(data)

    @staticmethod
    def write_stderr(data):
        """
        Overridable method to write to stderr, useful if you
        want to apply some kind of filter, or write to a file
        instead.
        :param data:
        :return:
        """
        sys.stderr.write(data)

    def _terminate_all(self):
        """
        Terminates all running processes
        :return:
        """
        print("Terminating processes...")
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
        self.streams[name] = (NBSR(self.procs[name].stdout, name),
                              NBSR(self.procs[name].stderr, name))

    def _launch_simulator(self, ready_str="World plugin loaded", output_tag="simulator"):
        """
        Launches the simulator
        :return:
        """
        print("Launching the simulator...")
        gz_args = self.simulator_cmd + self.simulator_args
        snapshot_world = os.path.join(
                self.snapshot_directory,
                self.snapshot_world_file)
        world = snapshot_world \
            if os.path.exists(snapshot_world) else self.world_file
        gz_args.append(world)
        self.procs[output_tag] = self._launch_with_ready_str(
                cmd=gz_args,
                ready_str=ready_str,
                output_tag=output_tag)
        self._add_output_stream(output_tag)

    def _launch_manager(self):
        """
        :return:
        """
        print("Launching experiment manager...")
        os.environ['PYTHONUNBUFFERED'] = 'True'
        args = self.manager_cmd + self.manager_args
        args += [self.restore_arg, self.restore_directory]
        process = subprocess.Popen(
                args,
                bufsize=1,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

        self.procs['manager'] = process
        self._add_output_stream('manager')

    @staticmethod
    def _launch_with_ready_str(cmd, ready_str, output_tag="simulator"):
        """
        :param cmd:
        :param ready_str:
        :return:
        """
        process = subprocess.Popen(
                cmd,
                bufsize=1,
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
            sys.stderr.write("Windows may not give the optimal experience\n")

        ready = False
        while not ready:
            exit_code = process.poll()
            if exit_code is not None:
                # flush out all stdout and stderr
                out, err = process.communicate()
                if out is not None:
                    sys.stdout.write("{}\n".format(out.decode('utf-8')))
                if err is not None:
                    sys.stderr.write("{}\n".format(err.decode('utf-8')))
                raise RuntimeError("Error launching {}, exit with code {}"
                                   .format(cmd, exit_code))

            try:
                out = process.stdout.readline().decode('utf-8')
                if len(out) > 0:
                    sys.stdout.write("[{}-launch] {}".format(output_tag, out))
                if ready_str in out:
                    ready = True
            except IOError:
                pass

            if not mswindows:
                try:
                    err = process.stderr.readline().decode('utf-8')
                    if len(err) > 0:
                        sys.stderr.write("[{}-launch] {}".format(output_tag, err))
                except IOError:
                    pass

            time.sleep(0.1)

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
            sys.stderr.write("Windows may not give the optimal experience\n")

        return process
