from __future__ import print_function
import subprocess
import os
import psutil
from datetime import datetime
import time
import sys
import atexit
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
    WorldManager. The supervisor launches subprocesses for (a) a world,
    (b) a body analyzer and (c) your manager / experiment. It determines
     a fixed output directory for this experiment run, which is provided
    to the manager with the `restore_arg` argument.

    The only way the experiment is considered finished is if (c) finishes with
    a zero exit code. If (a) or (b) shut down or (c) shuts down with a
    nonzero exit code, this is considered a failure, which will result in
    all processes being killed and restarted. When the manager is restarted,
    it will receive the given `restore_arg` with the snapshot directory,
    and it should restore the world state from there.
    """

    def __init__(self,
                 manager_cmd,
                 world_file,
                 output_directory=None,
                 manager_args=None,
                 gazebo_cmd="gzserver",
                 analyzer_cmd=None,
                 gazebo_args=None,
                 restore_arg="--restore-directory",
                 snapshot_world_file="snapshot.world",
                 restore_directory=None,
                 plugins_dir_path=None,
                 models_dir_path=None
                 ):
        """

        :param manager_cmd: The command used to run your manager / experiment
        :param world_file: Full path (or relative to cwd) to the Gazebo world file to be loaded.
        :param output_directory: Full path (or relative to cwd) to the output directory, which will
                                 be the parent of the restore directory.
        :param manager_args: Commands to pass to the manager
        :param gazebo_cmd: Command to run Gazebo with
        :param analyzer_cmd: Command to run the analyzer with, leave `None` for no analyzer.
        :param gazebo_args: Arguments to pass to Gazebo, *excluding* the world file name
        :param restore_arg: Argument used to pass the snapshot/restore directory name to
                            the manager. Note that the output directory is not passed as
                            part of this name, just the relative path.
        :param snapshot_world_file:
        :param restore_directory:
        :param plugins_dir_path: Full path (or relative to cwd) to the gazebo plugins directory
                                 (setting env variable GAZEBO_PLUGIN_PATH).
        :param models_dir_path: Full path (or relative to cwd) to the gazebo models directory
                                (setting env variable GAZEBO_MODEL_PATH).
        """
        self.restore_directory = datetime.now().strftime('%Y%m%d%H%M%S') \
            if restore_directory is None else restore_directory
        self.output_directory = 'output' \
            if output_directory is None else os.path.abspath(output_directory)
        self.snapshot_directory = os.path.join(self.output_directory, self.restore_directory)
        self.snapshot_world_file = snapshot_world_file
        self.restore_arg = restore_arg
        self.gazebo_args = gazebo_args if gazebo_args is not None else ["-u"]
        self.analyzer_cmd = analyzer_cmd if isinstance(analyzer_cmd, list) or not analyzer_cmd else [analyzer_cmd]
        self.gazebo_cmd = gazebo_cmd if isinstance(gazebo_cmd, list) else [gazebo_cmd]
        self.manager_args = manager_args if manager_args is not None else []
        self.manager_args += [self.restore_arg, self.snapshot_directory]

        self.world_file = os.path.abspath(world_file)
        self.manager_cmd = manager_cmd if isinstance(manager_cmd, list) else [manager_cmd]

        self.streams = {}
        self.procs = {}

        # Terminate all processes when the supervisor exits
        atexit.register(self._terminate_all)

        # Set plugins dir path for Gazebo
        if plugins_dir_path is not None:
            plugins_dir_path = os.path.abspath(plugins_dir_path)
            try:
                new_env_var = "{}:{}".format(os.environ["GAZEBO_PLUGIN_PATH"], plugins_dir_path)
            except KeyError:
                new_env_var = plugins_dir_path
            os.environ["GAZEBO_PLUGIN_PATH"] = new_env_var

        # Set models dir path for Gazebo
        if models_dir_path is not None:
            models_dir_path = os.path.abspath(models_dir_path)
            try:
                new_env_var = "{}:{}".format(os.environ["GAZEBO_MODEL_PATH"], models_dir_path)
            except KeyError:
                new_env_var = models_dir_path
            os.environ['GAZEBO_MODEL_PATH'] = new_env_var

        print("Created Supervisor with:"
              "\n\t- manager command: {} {}"
              "\n\t- gazebo command: {} {}"
              "\n\t- world file: {}"
              "\n\t- gazebo plugin dir: {}"
              "\n\t- gazebo models dir: {}"
              .format(manager_cmd,
                      manager_args,
                      gazebo_cmd,
                      gazebo_args,
                      world_file,
                      plugins_dir_path,
                      models_dir_path)
              )

    def launch_gazebo(self):
        self._launch_gazebo()

        # Wait for the end
        ret = 0
        for proc_name in self.procs:
            ret = self.procs[proc_name].wait()
            if ret == 0:
                sys.stdout.write("Program {} exited normally\n".format(proc_name))
                ret = 255
            else:
                sys.stderr.write("Program {} exited with code {}\n".format(proc_name, ret))

        return ret

    def launch(self):
        """
        (Re)launches the experiment.
        :return:
        """
        if not os.path.exists(self.output_directory):
            os.mkdir(self.output_directory)
        if not os.path.exists(self.snapshot_directory):
            os.mkdir(self.snapshot_directory)

        success = False
        while not success:
            print("Launching all processes...")
            self._launch_analyzer()
            self._launch_gazebo()
            self._launch_manager()

            while not success:
                # Write out all received stdout
                self._pass_through_stdout()
                manager_code = self.procs['manager'].poll()
                success = (manager_code == 0)
                unrecoverable = (manager_code == 23)

                if manager_code and unrecoverable:
                    print("Manager has exited with unrecoverable status code, terminating.", file=sys.stderr)
                    self._terminate_all()
                    sys.exit(1)

                if manager_code and not success:
                    print("Manager has exited with status code %d, restarting experiment..." % int(manager_code))
                    break

                if 'analyzer' in self.procs and self.procs['analyzer'].poll() is not None:
                    print("Analyzer has exited, restarting experiment...")
                    break

                if 'gazebo' in self.procs and self.procs['gazebo'].poll() is not None:
                    print("Gazebo has exited, restarting experiment...")
                    break

                # We could do this a lot less often, but this way we get
                # output once every second.
                time.sleep(1.0)

            print("Stop condition reached.")
            self._terminate_all()

        print("Experiment successful, shutting down.")

    def _pass_through_stdout(self):
        """
        Passes process piped standard out through to normal stdout
        :return:
        """
        for stdout, stderr in self.streams.values():
            try:
                for _ in range(1000):
                    out = stdout.readline(0.005)
                    err = stderr.readline(0.005)

                    if not out and not err:
                        break

                    if out:
                        self.write_stdout(out)

                    if err:
                        self.write_stderr(err)
            except:
                pass

    def write_stdout(self, data):
        """
        Overridable method to write to stdout, useful if you
        want to apply some kind of filter, or write to a file
        instead.
        :param data:
        :return:
        """
        sys.stdout.write(data)

    def write_stderr(self, data):
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
        for proc in self.procs.values():
            if proc.poll() is None:
                terminate_process(proc)

        self.procs = {}

    def _add_output_stream(self, name):
        """
        Creates a non blocking stream reader for the process with
        the given name, and adds it to the streams that are passed
        through.
        :param name:
        :return:
        """
        self.streams[name] = (NBSR(self.procs[name].stdout), NBSR(self.procs[name].stderr))

    def _launch_analyzer(self, ready_str="Body analyzer ready"):
        """
        Launches the analyzer.
        :return:
        """
        if not self.analyzer_cmd:
            return

        print("Launching analyzer...")
        self.procs['analyzer'] = self._launch_with_ready_str(self.analyzer_cmd, ready_str)
        self._add_output_stream('analyzer')

    def _launch_gazebo(self, ready_str="World plugin loaded"):
        """
        Launches Gazebo
        :return:
        """
        print("Launching Gazebo...")
        gz_args = self.gazebo_cmd + self.gazebo_args
        snapshot_world = os.path.join(self.snapshot_directory, self.snapshot_world_file)
        world = snapshot_world if os.path.exists(snapshot_world) else self.world_file
        gz_args.append(world)
        self.procs['gazebo'] = self._launch_with_ready_str(gz_args, ready_str)
        self._add_output_stream('gazebo')

    def _launch_manager(self):
        """
        :return:
        """
        print("Launching experiment manager...")
        args = self.manager_cmd + self.manager_args
        args += [self.restore_arg, self.restore_directory]
        self.procs['manager'] = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self._add_output_stream('manager')

    @staticmethod
    def _launch_with_ready_str(cmd, ready_str):
        """
        :param cmd:
        :param ready_str:
        :return:
        """
        process = subprocess.Popen(cmd, bufsize=0, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # make out and err non-blocking pipes
        if not mswindows:
            import fcntl
            for pipe in [process.stdout, process.stderr]:
                fd = pipe.fileno()
                fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
        else:
            sys.stderr.write("Using Windows may not give the most optimal experience\n")
            # hint on how to fix it here: https://github.com/cs01/gdbgui/issues/18#issuecomment-284263708

        ready = False
        while not ready:
            exit_code = process.poll()
            if exit_code is not None:
                # flush out all stdout and stderr
                out, err = process.communicate()
                if out is not None:
                    sys.stdout.write(out)
                if err is not None:
                    sys.stderr.write(err)
                raise RuntimeError("Error launching launch {}, exit with code {}".format(cmd, exit_code))

            try:
                out = process.stdout.readline()
                sys.stdout.write(out)
                if ready_str in out:
                    ready = True
            except IOError:
                pass

            if not mswindows:
                try:
                    err = process.stderr.readline()
                    sys.stderr.write(err)
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
            sys.stderr.write("Using Windows may not give the most optimal experience\n")
            # hint on how to fix it here: https://github.com/cs01/gdbgui/issues/18#issuecomment-284263708

        return process
