import random
import uuid

import asyncio
from typing import AnyStr, Callable, Any, Tuple, Optional, Iterable

import celery
import celery.exceptions
import math

from pyrevolve.SDF.math import Vector3
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.tol.manage.measures import BehaviouralMeasurements
from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase
from pyrevolve.util.supervisor.rabbits import RobotState
from pyrevolve.util import Time

app = celery.Celery('CeleryQueue', backend='rpc://', broker='pyamqp://guest@localhost//')


@app.task
def evaluate_robot(robot_sdf: AnyStr, life_timeout: float):
    raise NotImplementedError("Evaluating a robot is implemented in C++, inside gazebo")


class CeleryQueue:
    EVALUATION_TIMEOUT = 360  # SECONDS
    MAX_ATTEMPTS = 3

    def __init__(self, args, queue_name: AnyStr = 'celery', n_workers: int = 1):
        self._queue_name: AnyStr = queue_name
        self._n_workers: int = n_workers
        self._args = args
        self._dbname: AnyStr = str(uuid.uuid1())
        self._db: PostgreSQLDatabase = PostgreSQLDatabase(dbname=self._dbname, address='localhost')

    def change_n_workers(self, n: int):
        raise NotImplementedError("Cannot change the number of workers yet")
        self._n_workers = n
        # TODO increase workers
        # TODO kill some workers

    async def start(self):
        # TODO start workers
        self._db.start()
        self._db.init_db(first_time=False)

    async def stop(self):
        # TODO STOP workers
        self._db.disconnect()
        self._db.destroy()

    async def _wait_for_response(self, celery_task) -> Tuple[Optional[float], Optional[BehaviouralMeasurements]]:
        """
        Start this task separately, hopefully this will not lock the entire process
        :param celery_task:
        :return:
        """
        fitness: float = celery_task.get(timeout=self.EVALUATION_TIMEOUT)

        # TODO get DB_ID from rabbitmq and retrieve result from database
        # behaviour = session.query(DBBehaviour)
        # fitness: float = fitness_fun(behaviour, robot)

        return fitness, None

    async def test_robot(self,
                         individual: Individual,
                         robot: RevolveBot,
                         conf: PopulationConfig,
                         fitness_fun: Callable[[Any, RevolveBot], float]) \
            -> Tuple[Optional[float], Optional[BehaviouralMeasurements]]:
        """
        Sends a robot to be evaluated in the rabbitmq
        :param individual: unused
        :param robot: RevolveBot to analyze
        :param conf: configuration object with some parameters about evaluation time and grace time
        :param fitness_fun: unused
        :return: Fitness and Behaviour
        """

        for attempt in range(self.MAX_ATTEMPTS):
            pose_z: float = self._args.z_start
            if robot.simulation_boundaries is not None:
                pose_z -= robot.simulation_boundaries.min.z
            pose: Vector3 = Vector3(0.0, 0.0, pose_z)
            robot_sdf: AnyStr = robot.to_sdf(pose)
            max_age: float = conf.evaluation_time + conf.grace_time

            import xml.dom.minidom
            reparsed = xml.dom.minidom.parseString(robot_sdf)
            robot_name = ''
            for model in reparsed.documentElement.getElementsByTagName('model'):
                robot_name = model.getAttribute('name')
                if str(robot_name).isdigit():
                    error_message = f'Inserting robot with invalid name: {robot_name}'
                    logger.critical(error_message)
                    raise RuntimeError(error_message)
                logger.info("Inserting robot {}.".format(robot_name))

            r = evaluate_robot.delay(robot_sdf, max_age)
            logger.info("Request sent to rabbitmq: ", str(r))

            try:
                robot_id: int = await asyncio.create_task(self._wait_for_response(r))
            except celery.exceptions.TimeoutError:
                logger.warning(f'Giving up on robot {robot_name} after {self.EVALUATION_TIMEOUT} seconds.')
                if attempt < self.MAX_ATTEMPTS:
                    logger.warning(f'Retrying')
                continue

            # DB_ID from rabbitmq and retrieve result from database
            with self._db.session() as session:
                # behaviour = [s for s in session.query(RobotState).filter(RobotState.evaluation_robot_id == robot_id)]
                behaviour_query: Iterable[RobotState] = session.query(RobotState).filter(RobotState.evaluation_robot_id == robot_id)
                first_pos: Optional[Vector3] = None
                first_time: Time
                last_pos: Optional[Vector3] = None
                last_time: Time
                for state in behaviour_query:
                    state: RobotState = state
                    print(f"STATE of robot {state.robot.name}: ({state.pos_x};{state.pos_y};{state.pos_z})"
                          f" - ({state.rot_quaternion_x};{state.rot_quaternion_y};{state.rot_quaternion_z};{state.rot_quaternion_w})")
                    last_time = Time(sec=state.time_sec, nsec=state.time_nsec)
                    last_pos = Vector3(state.pos_x, state.pos_y, state.pos_z)
                    if first_pos is None:
                        first_time = last_time
                        first_pos = last_pos.copy()

                # TODO fitness: float = fitness_fun(behaviour, robot)
                distance: Vector3 = last_pos - first_pos
                distance_size: float = math.sqrt(distance.x*distance.x + distance.y*distance.y)
                fitness: float = distance_size / float(last_time - first_time)

            return fitness, BehaviouralMeasurements()

        logger.warning(f'Robot {robot.id} evaluation failed (reached max attempt of {self.MAX_ATTEMPTS}),'
                       f'fitness set to None.')
        robot_fitness_none = None
        measurements_none = None
        return robot_fitness_none, measurements_none
