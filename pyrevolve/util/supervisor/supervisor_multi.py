from __future__ import absolute_import
from __future__ import print_function

import atexit
import subprocess
import os
import psutil
import sys
import asyncio
import platform

from datetime import datetime

from ...custom_logging.logger import create_logger
from ...custom_logging.logger import logger as revolve_logger

from .stream import PrettyStreamReader

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
                 simulator_name='simulator',
                 process_terminated_callback=None,
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
        :param process_terminated_callback: Callback to execute when a process dies
        :type process_terminated_callback: lambda (process, ret_code) -> None
        """
        if mswindows:
            text = "Starting the simulator with WINDOWS may cause issues! BEWARE!!!"
            revolve_logger.error(text)
            print(text, file=sys.stderr)

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
        self._logger = create_logger(simulator_name)
        self._process_terminated_callback = process_terminated_callback
        self._process_terminated_futures = []

        # Terminate all processes when the supervisor exits
        atexit.register(lambda:
                        asyncio.get_event_loop().run_until_complete(self._terminate_all())
                        )

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
                          f"\n\t- simulator command: {simulator_cmd} {simulator_args}"
                          f"\n\t- world file: {world_file}"
                          f"\n\t- GAZEBO_PLUGIN_PATH: {plugins_dir_path}"
                          f"\n\t- GAZEBO_MODEL_PATH: {models_dir_path}")

    async def launch_simulator(self, address='localhost', port=11345):
        """
        Launches the simulator process
        :param address:
        :param port:
        """
        await self._launch_simulator(output_tag=self._simulator_name, address=address, port=port)
        self._enable_process_terminate_callbacks()

    async def relaunch(self, sleep_time=1, address='localhost', port=11345):
        """
        Stops and restarts the process, waiting `sleep_time` in between
        :param sleep_time:
        :param address:
        :param port:
        """
        await self.stop()
        await asyncio.sleep(sleep_time)
        await self.launch_simulator(address=address, port=port)

    async def stop(self):
        """
        Stops the simulator and all other process (companion and children processes)
        """
        self._disable_process_terminate_callbacks()
        await self._terminate_all()

    async def _terminate_all(self):
        """
        Terminates all running processes and sub-processes
        """
        self._logger.info("Terminating processes...")
        for proc in list(self.procs.values()):
            try:
                if proc.returncode is None:
                    terminate_process(proc)
            except psutil.NoSuchProcess:
                self._logger.debug(f'Cannot terminate already dead process "{proc}"')

        # flush output of all processes
        await self._flush_output_streams()

        for proc in self.procs.values():
            retcode = await proc.wait()
            self._logger.info(f'Process exited with code {retcode}')

        self.procs = {}

    async def _flush_output_streams(self):
        """
        Waits until all streams in this supervisor are at EOF
        """
        for out, err in self.streams.values():
            await out
            await err

    def _add_output_stream(self, name):
        """
        Creates an async stream reader for the process with
        the given name, and adds it to the streams that are passed
        through.
        :param name:
        """
        process = self.procs[name]

        stdout = PrettyStreamReader(process.stdout)
        stderr = PrettyStreamReader(process.stderr)

        async def poll_output(stream, logger):
            while not stream.at_eof():
                line = await stream.readline()
                logger(line)

        self.streams[name] = (
            asyncio.ensure_future(poll_output(stdout, self._logger.info)),
            asyncio.ensure_future(poll_output(stderr, self._logger.error)),
        )

    async def _launch_simulator(self, ready_str="World plugin loaded", output_tag="simulator", address='localhost',
                          port=11345):
        """
        Launches the simulator
        """

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
        env['GAZEBO_MASTER_URI'] = f'http://{address}:{port}'

        process = subprocess.run(['which', self.simulator_cmd[0]], stdout=subprocess.PIPE)
        process.check_returncode()
        gazebo_libraries_path = process.stdout.decode()
        gazebo_libraries_path = os.path.dirname(gazebo_libraries_path)
        for lib_f in ['lib', 'lib64']:
            _gazebo_libraries_path = os.path.join(gazebo_libraries_path, '..', lib_f)
            lib_postfix = 'dylib' if platform.system() == 'Darwin' else 'so'
            if os.path.isfile(os.path.join(_gazebo_libraries_path, f'libgazebo_common.{lib_postfix}')):
                gazebo_libraries_path = _gazebo_libraries_path
                break

        if platform.system() == 'Darwin':
            env['DYLD_LIBRARY_PATH'] = gazebo_libraries_path
        else:  # linux
            env['LD_LIBRARY_PATH'] = gazebo_libraries_path
        self.procs[output_tag] = await self._launch_with_ready_str(
            cmd=gz_args,
            ready_str=ready_str,
            env=env)
        self._add_output_stream(output_tag)

    def _enable_process_terminate_callbacks(self):
        for proc in self.procs.values():
            dead_process_future = asyncio.ensure_future(proc.wait())

            def create_callback(_process):
                def _callback(ret_code):
                    if self._process_terminated_callback is not None:
                        self._process_terminated_callback(_process, ret_code)
                return _callback

            dead_process_future.add_done_callback(create_callback(proc))
            self._process_terminated_futures.append(dead_process_future)

    def _disable_process_terminate_callbacks(self):
        for dead_process_future in self._process_terminated_futures:
            dead_process_future.cancel()
        self._process_terminated_futures.clear()

    async def _launch_with_ready_str(self, cmd, ready_str, env):

        process = await asyncio.create_subprocess_exec(
            cmd[0],
            *cmd[1:],
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout = PrettyStreamReader(process.stdout)
        stderr = PrettyStreamReader(process.stderr)

        ready_str_found = asyncio.Future()

        class SimulatorEnded(Exception):
            pass

        async def read_stdout():
            while not ready_str_found.done():
                if process.returncode is None:
                    ready_str_found.set_exception(SimulatorEnded())
                out = await stdout.readline()
                self._logger.info(f'[starting] {out}')
                if ready_str in out:
                    ready_str_found.set_result(None)

        async def read_stderr():
            while not ready_str_found.done() and process.returncode is None:
                err = await stderr.readline()
                if err:
                    self._logger.error(f'[starting] {err}')

        stdout_async = asyncio.ensure_future(read_stdout())
        stderr_async = asyncio.ensure_future(read_stderr())

        try:
            await ready_str_found
        except SimulatorEnded:
            pass
        finally:
            await stdout_async
            await stderr_async

        if process.returncode is not None:
            await process.wait()
            while not process.stdout.at_eof():
                self._logger.info(await stdout.readline())
            while not process.stderr.at_eof():
                self._logger.error(await stderr.readline())
            await asyncio.sleep(0.1)
            raise RuntimeError(f'Process "{cmd[0]}" exited before it was ready. Exit code {process.returncode}')

        return process
