import os

from pyrevolve.custom_logging.logger import logger
from pyrevolve.gazebo.analyze import BodyAnalyzer
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.util.supervisor.supervisor_collision import CollisionSimSupervisor


class AnalyzerQueue(SimulatorQueue):
    EVALUATION_TIMEOUT = 30  # seconds

    def __init__(self, n_cores: int, settings, port_start=11345):
        super(AnalyzerQueue, self).__init__(n_cores, settings, port_start)

    @staticmethod
    def _simulator_supervisor(world, simulator_cmd, simulator_name_postfix):
        return CollisionSimSupervisor(
            world_file=os.path.join('tools', 'analyzer', 'analyzer-world.world'),
            simulator_cmd=simulator_cmd,
            simulator_args=["--verbose"],
            plugins_dir_path=os.path.join('.', 'build', 'lib'),
            models_dir_path=os.path.join('.', 'models'),
            simulator_name=f'analyzer_{simulator_name_postfix}'
        )

    async def _connect_to_simulator(self, settings, address, port):
        return await BodyAnalyzer.create(address, port)

    async def _evaluate_robot(self, simulator_connection, robot, conf):
        if robot.failed_eval_attempt_count == 3:
            logger.info(f'Robot {robot.phenotype.id} analyze failed (reached max attempt of 3), fitness set to None.')
            analyze_result = None
            return analyze_result
        else:
            analyze_result = await simulator_connection.analyze_robot(robot.phenotype)
            return analyze_result
