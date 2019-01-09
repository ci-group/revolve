import os
import atexit
import shutil
import datetime
from . import Supervisor

class VREPSupervisor(Supervisor):
    def __init__(self,
                 manager_cmd,
                 world_file,
                 output_directory=None,
                 restore_directory=None,
                 snapshot_world_file="snapshot.world",
                 manager_args=None,
                 vrep_cmd="vrep",
                 vrep_args=None,
                 vrep_folder=None,
                 plugins_dir_path=None,
                 models_dir_path=None):
        """
        :param manager_cmd: The command used to run your manager / experiment
        :param world_file: Full path (or relative to cwd) to the world file 
                           to load.
        :param manager_args: Commands to pass to the manager
        :param vrep_cmd: Command to run VREP with
        :param vrep_args: Arguments to VREP
        :param vrep_folder: Folder where to create the link to plugins and models
        :param plugins_dir_path: Full path (or relative to cwd) to the VREP
                                 plugins directory (creating a link into the vrep folder).
        :param models_dir_path: Full path (or relative to cwd) to the VREP
                                models directory (creating a link into the vrep folder).
        """
        self.restore_directory = datetime.datetime.now().strftime('%Y%m%d%H%M%S') \
            if restore_directory is None else restore_directory
        self.output_directory = 'output' \
            if output_directory is None else os.path.abspath(output_directory)
        self.snapshot_directory = os.path.join(
                self.output_directory,
                self.restore_directory)
        self.snapshot_world_file = snapshot_world_file
        self.restore_arg = None
        self.analyzer_cmd = None
        self.world_file = os.path.abspath(world_file)
        if vrep_folder is not None:
            self.vrep_folder = os.path.abspath(vrep_folder)
        else:
            self.vrep_folder = os.path.dirname(shutil.which(vrep_cmd))

        # VREP command and arguments
        self.gazebo_cmd = [vrep_cmd]
        self.gazebo_args = vrep_args if vrep_args is not None else [] 

        # Manager command and arguments
        self.manager_cmd = manager_cmd \
            if isinstance(manager_cmd, list) else [manager_cmd]
        self.manager_args = manager_args if manager_args is not None else []

        self.streams = {}
        self.procs = {}

        # Terminate all processes when the supervisor exits
        atexit.register(self._terminate_all)
        atexit.register(self._remove_vrep_links)

        revolve_folder = os.path.join(self.vrep_folder, "revolve")
        try:
            os.mkdir(revolve_folder)
        except FileExistsError:
            print("{} folder already exists".format(revolve_folder))

        # Set plugins link
        if plugins_dir_path is not None:
            self.plugins_dir_path = os.path.abspath(plugins_dir_path)
            #TODO for libv_repExt* in `plugins_dir_path` create a link into vrep folder

        # Set models dir path for Gazebo
        if models_dir_path is not None:
            self.models_dir_path = os.path.abspath(models_dir_path)
            self.models_dir_path_link = os.path.join(revolve_folder, "models")
            if os.path.islink(self.models_dir_path_link):
                os.remove(self.models_dir_path_link)
            os.symlink(src=self.models_dir_path,
                       dst=self.models_dir_path_link,
                       target_is_directory=True)

        print("Created VREP Supervisor with:"
              "\n\t- manager command: {} {}"
              "\n\t- vrep command: {} {}"
              "\n\t- world file: {}"
              "\n\t- vrep plugin dir: {}"
              "\n\t- vrep models dir: {}"
              .format(manager_cmd,
                      manager_args,
                      vrep_cmd,
                      vrep_args,
                      world_file,
                      self.plugins_dir_path,
                      self.models_dir_path)
              )

    def _remove_vrep_links(self):
        """
        Cleanup revolve links in VREP
        :return:
        """
        os.remove(self.plugins_dir_path_link)
        os.remove(self.models_dir_path_link)

    def _launch_gazebo(self, ready_str="World plugin loaded"):
        """
        Launches Gazebo
        :return:
        """
        print("Launching VREP...")
        gz_args = self.gazebo_cmd + self.gazebo_args
        snapshot_world = os.path.join(
                self.snapshot_directory,
                self.snapshot_world_file)
        world = snapshot_world \
            if os.path.exists(snapshot_world) else self.world_file
        gz_args.append(world)
        self.procs['vrep'] = self._launch_with_ready_str(
                cmd=gz_args,
                ready_str=ready_str,
                output_tag="vrep")
        self._add_output_stream('vrep')
