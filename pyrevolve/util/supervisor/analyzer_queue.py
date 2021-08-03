import os
from typing import Callable

from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.population import PopulationConfig
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.gazebo.analyze import BodyAnalyzer
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.tol.manage.robotmanager import RobotManager
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.util.supervisor.supervisor_collision import CollisionSimSupervisor


class AnalyzerQueue(SimulatorQueue):
    EVALUATION_TIMEOUT = 30  # seconds

    def __init__(
        self, n_cores: int, settings, port_start=11345, simulator_cmd="gzserver"
    ):
        super(AnalyzerQueue, self).__init__(
            n_cores, settings, port_start, simulator_cmd
        )
        self._enable_play_pause = False

    def _simulator_supervisor(self, simulator_name_postfix):
        return CollisionSimSupervisor(
            world_file=os.path.join("tools", "analyzer", "analyzer-world.world"),
            simulator_cmd=self._simulator_cmd,
            simulator_args=["--verbose"],
            plugins_dir_path=os.path.join(".", "build", "lib"),
            models_dir_path=os.path.join(".", "models"),
            simulator_name=f"analyzer_{simulator_name_postfix}",
        )

    async def _connect_to_simulator(self, settings, address, port):
        return await BodyAnalyzer.create(address, port)

    async def _evaluate_robot(
        self,
        simulator_connection,
        robot: RevolveBot,
        conf: PopulationConfig,
        _fitness_fun: Callable[[RobotManager, RevolveBot], float],
    ):
        if robot.failed_eval_attempt_count == 3:
            logger.info(
                f"Robot {robot.phenotype.id} analyze failed (reached max attempt of 3), fitness set to None."
            )
            analyze_result = None
            return analyze_result
        else:
            analyze_result = await simulator_connection.analyze_robot(robot)
            return analyze_result
