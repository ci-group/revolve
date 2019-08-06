from .supervisor_multi import DynamicSimSupervisor


class CollisionSimSupervisor(DynamicSimSupervisor):
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
                 simulator_name='collision',
                 process_terminated_callback=None,
                 ):
        super().__init__(world_file,
                         output_directory,
                         simulator_cmd,
                         simulator_args,
                         restore_arg,
                         snapshot_world_file,
                         restore_directory,
                         plugins_dir_path,
                         models_dir_path,
                         simulator_name,
                         process_terminated_callback)

    async def _launch_simulator(self,
                                ready_str="Body analyzer ready",
                                output_tag="simulator",
                                address='localhost',
                                port=11345):
        return await super()._launch_simulator(ready_str, output_tag, address, port)
