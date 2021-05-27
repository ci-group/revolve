import atexit
import os.path
import platform
import re
import subprocess
import sys
from asyncio import Future

from asyncio.subprocess import Process
from typing import AnyStr, Optional, List, Dict, Callable, Tuple

import asyncio
import psutil

from pyrevolve.custom_logging.logger import logger as revolve_logger, create_logger
from pyrevolve.util.services import Service
from pyrevolve.util.supervisor.stream import PrettyStreamReader, StreamEnded


def terminate_process(pid: int) -> None:
    """
    Recursively kills a process and all of its children
    :param pid: process ID to recursively kill

    Inspired by http://stackoverflow.com/a/25134985/358873

    TODO Check if terminate fails and kill instead?
    """
    process = psutil.Process(pid)
    for child in process.children(recursive=True):
        child.terminate()

    process.terminate()


class GazeboCeleryWorkerSupervisor:
    """
    Utility class to easily start a gazebo celery worker on the current node
    """
    DEFAULT_ADDRESS: AnyStr = 'localhost'
    DEFAULT_PORT: int = 11345

    def __init__(self,
                 world_file: AnyStr,
                 gui: bool = False,
                 simulator_args: Optional[List[AnyStr]] = None,
                 plugins_dir_path: Optional[AnyStr] = None,
                 models_dir_path: Optional[AnyStr] = None,
                 simulator_name: AnyStr = 'GazeboCeleryWorker',
                 process_terminated_callback: Optional[Callable[[Process, int], None]] = None,
                 ):
        """

        :param world_file: Full path (or relative to cwd) to the Gazebo world
                           file to load.
        :param gui: If to start gazebo with or without gui
        :param simulator_args: Arguments to the Simulator, *excluding* the world file name
        :param plugins_dir_path: Full path (or relative to cwd) to the simulator
                                 plugins directory (setting env variable
                                 GAZEBO_PLUGIN_PATH).
        :param models_dir_path: Full path (or relative to cwd) to the simulator
                                models directory (setting env variable
                                GAZEBO_MODEL_PATH).
        :param process_terminated_callback: Callback to execute when a process dies
        """
        if sys.platform == "win32":
            text = "Starting the gazebo worker on WINDOWS may cause issues! BEWARE!!!!"
            revolve_logger.error(text)
            print(text, file=sys.stderr)

        self._simulator_args: List[AnyStr] = simulator_args if simulator_args is not None else []
        self._simulator_cmd: AnyStr = "gazebo" if gui else "gzserver"
        self._simulator_name: AnyStr = simulator_name

        self._world_file: AnyStr = os.path.abspath(world_file)

        self._streams: Dict[AnyStr, Tuple[PrettyStreamReader, PrettyStreamReader]] = {}
        self._procs: Dict[AnyStr, Process] = {}
        self._logger = create_logger(simulator_name)
        self._process_terminated_callback: Optional[Callable[[Process, int], None]] = process_terminated_callback
        self._process_terminated_futures: List[Future] = []

        self._rabbitmq_service = Service("RabbitMQ")

        # Terminate all processes when the supervisor exits
        atexit.register(lambda:
                        asyncio.get_event_loop().run_until_complete(self.stop())
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
                          f"\n\t- simulator command: {self._simulator_cmd} {self._simulator_args}"
                          f"\n\t- world file: {world_file}"
                          f"\n\t- export GAZEBO_PLUGIN_PATH={plugins_dir_path}"
                          f"\n\t- export GAZEBO_MODEL_PATH={models_dir_path}")

    async def launch_simulator(self, address: AnyStr = DEFAULT_ADDRESS, port: int = DEFAULT_PORT) -> None:
        """
        Launches the simulator process
        :param address: address the simulator should listen on
        :param port: port the simulator should listen on
        """
        await self._launch_simulator(output_tag=self._simulator_name, address=address, port=port)
        self._enable_process_terminate_callbacks()

    async def relaunch(self, sleep_time=1, address: AnyStr = DEFAULT_ADDRESS, port: int = DEFAULT_PORT) -> None:
        """
        Stops and restarts the process, waiting `sleep_time` in between
        :param sleep_time: sleep time in seconds between process exit and restart
        :param address: address the simulator should listen on
        :param port: port the simulator should listen on
        """
        await self.stop()
        await asyncio.sleep(sleep_time)
        await self.launch_simulator(address=address, port=port)

    async def stop(self) -> None:
        """
        Stops the simulator and all other processes (companion and children processes)
        """
        self._disable_process_terminate_callbacks()
        await self._terminate_all()

    async def wait(self) -> None:
        """
        Waiting until all processes are done
        """
        for proc in self._procs.values():
            await proc.wait()
        #asyncio.wait(waits, return_when=asyncio.ALL_COMPLETED)

    async def _terminate_all(self) -> None:
        """
        Terminates all running processes and sub-processes
        """
        self._logger.info("Terminating processes...")
        for proc in list(self._procs.values()):
            proc: Process
            try:
                if proc.returncode is None:
                    terminate_process(proc.pid)
            except psutil.NoSuchProcess:
                self._logger.debug(f'Cannot terminate already dead process "{proc}" (PID: {proc.pid})')

        # flush output of all processes
        await asyncio.wait_for(self._flush_output_streams(), timeout=10)

        for proc in self._procs.values():
            ret_code = await proc.wait()
            self._logger.info(f'Process exited with code {ret_code}')

        self._procs = {}

    async def _flush_output_streams(self) -> None:
        """
        Waits until all streams in this supervisor are at EOF
        """
        for out, err in self._streams.values():
            await out
            await err

    def _add_output_stream(self, name: AnyStr) -> None:
        """
        Creates an async stream reader for the process wit
        the given name, and adds it to the streams that are passed
        through.
        :param name:
        """
        process: Process = self._procs[name]

        stdout = PrettyStreamReader(process.stdout)
        stderr = PrettyStreamReader(process.stderr)

        async def poll_output(stream, logger):
            while not stream.at_eof():
                line = await stream.readline()
                logger(line)

        self._streams[name] = (
            asyncio.ensure_future(poll_output(stdout, self._logger.info)),
            asyncio.ensure_future(poll_output(stderr, self._logger.error)),
        )

    async def _launch_simulator(self,
                                ready_str="Started Gazebo worker with tag: ",
                                output_tag="simulator",
                                address=DEFAULT_ADDRESS,
                                port=DEFAULT_PORT) -> None:
        """
        Launches the simulator and waits for the plugin to be loaded.
        :param ready_str: Message from the plugin to wait for.
        :param output_tag: "name" of the simulator in the log
        :param address: address the simulator should listen on
        :param port: port the simulator should listen on
        """
        self._logger.info("Ensuring the RabbitMQ service is running")
        if not self._rabbitmq_service.is_running():
            await self._rabbitmq_service.start()
            # TODO wait until it accepts connections instead of waiting 5 seconds
            await asyncio.sleep(5)

        self._logger.info("Launching the simulator...")
        gz_args: List[AnyStr] = [self._simulator_cmd] + self._simulator_args
        gz_args.append('--world')
        gz_args.append(self._world_file)

        env = {}
        for key, value in os.environ.items():
            env[key] = value
        env['GAZEBO_MASTER_URI'] = f'http://{address}:{port}'

        # Search for gazebo dynamic library lookup folder
        process = subprocess.run(['which', self._simulator_cmd], stdout=subprocess.PIPE)
        process.check_returncode()
        gazebo_libraries_path: AnyStr = os.path.dirname(process.stdout.decode())
        for lib_f in ['lib', 'lib64']:
            _gazebo_libraries_path = os.path.join(gazebo_libraries_path, '..', lib_f)
            lib_postfix = 'dylib' if platform.system() == 'Darwin' else 'so'
            libfile_hypotesys: AnyStr = os.path.join(_gazebo_libraries_path, f'libgazebo_common.{lib_postfix}')
            if os.path.isfile(libfile_hypotesys):
                gazebo_libraries_path = _gazebo_libraries_path
                break
        else:
            self._logger.error("Gazebo library folder not found")

        # Platform dependant environment setup
        if platform.system() == 'Darwin':
            env['DYLD_LIBRARY_PATH'] = gazebo_libraries_path
            self._logger.info(f'DYLD_LIBRARY_PATH={gazebo_libraries_path}')
        elif platform.system() == 'Linux':
            env['LD_LIBRARY_PATH'] = gazebo_libraries_path
            self._logger.info(f'LD_LIBRARY_PATH={gazebo_libraries_path}')
            # remove screen scaling variables, gazebo does not handle screen scaling really well.
            if 'QT_AUTO_SCREEN_SCALE_FACTOR' in env:
                del env['QT_AUTO_SCREEN_SCALE_FACTOR']
            if 'QT_SCREEN_SCALE_FACTORS' in env:
                del env['QT_SCREEN_SCALE_FACTORS']
            # force set x11(xcb) platform, since gazebo on wayland is broken
            env['QT_QPA_PLATFORM'] = 'xcb'
        else:
            self._logger.warning(f'Platform "{platform.system()}" not recognized, cannot set library path.')

        # Preparations ready, starting the simulator
        self._procs[output_tag] = await self._launch_with_ready_str(
            cmd=gz_args,
            ready_str=ready_str,
            env=env
        )

        # Add output streams
        self._add_output_stream(output_tag)

    def _enable_process_terminate_callbacks(self) -> None:
        """
        Enables callbacks for when one of the processes exits (normally or not)
        """
        for proc in self._procs.values():
            dead_process_future = asyncio.ensure_future(proc.wait())

            def create_callback(_process: Process):
                def _callback(ret_code: int):
                    if self._process_terminated_callback is not None:
                        self._process_terminated_callback(_process, ret_code)
                return _callback

            dead_process_future.add_done_callback(create_callback(proc))
            self._process_terminated_futures.append(dead_process_future)

    def _disable_process_terminate_callbacks(self) -> None:
        """
        Disable callbacks for when processes exit.
        Useful in case the simulator is about to get closed on purpose.
        """
        for deaed_process_future in self._process_terminated_futures:
            deaed_process_future.cancel()
        self._process_terminated_futures.clear()

    async def _launch_with_ready_str(self, cmd: List[AnyStr], ready_str: AnyStr, env: Dict[AnyStr, AnyStr]) -> Process:
        """
        Launches a process and waits until the ready string has been "printed" by the program,
        indicating that the plugin loaded correctly
        :param cmd:
        :param ready_str: Message to expect "printed" from the Gazebo plugin
        :param env:
        :return:
        """
        process: Process = await asyncio.create_subprocess_exec(
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
                try:
                    if process.returncode is not None:
                        ready_str_found.set_exception(SimulatorEnded())
                        return
                    out = await stdout.readline()
                    self._logger.info(f'[starting] {out}')
                    if ready_str in out:
                        ready_str_found.set_result(out)
                except StreamEnded as e:
                    ready_str_found.set_exception(e)
                    return

        async def read_stderr():
            while not ready_str_found.done() and process.returncode is None:
                try:
                    err = await stderr.readline()
                    if err:
                        self._logger.error(f'[starting] {err}')
                except StreamEnded as e:
                    ready_str_found.set_exception(e)
                    return

        stdout_async = asyncio.ensure_future(read_stdout())
        stderr_async = asyncio.ensure_future(read_stderr())

        try:
            await ready_str_found
            ready_text: AnyStr = ready_str_found.result()
            extract_tag = re.compile(f'.*{ready_str}(.*)')
            match = extract_tag.match(ready_text)
            if match is not None:
                self.rabbit_consumer_tag: AnyStr = match.group(1)
                self._logger.info(f"Recognized worker with tag: {self.rabbit_consumer_tag}")
        except (SimulatorEnded, StreamEnded):
            await asyncio.sleep(0.1)

        stderr_async.cancel()
        stdout_async.cancel()
        try:
            await stderr_async
        except (asyncio.CancelledError, StreamEnded):
            await asyncio.sleep(0.1)
        try:
            await stdout_async
        except (asyncio.CancelledError, StreamEnded):
            await asyncio.sleep(0.1)

        if process.returncode is not None:
            await process.wait()
            while not process.stdout.at_eof():
                self._logger.info(await stdout.readline())
            while not process.stderr.at_eof():
                self._logger.error(await stderr.readline())
            await asyncio.sleep(0.1)
            raise RuntimeError(f'Process "{cmd[0]}" exited before it was ready. Exit code {process.returncode}')

        return process
