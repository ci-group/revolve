import asyncio
import os
import time

from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.population import PopulationConfig
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import measures


class SimulatorSimpleQueue:
    def __init__(self, n_cores: int, settings, port_start=11345):
        assert (n_cores > 0)
        self._n_cores = n_cores
        self._settings = settings
        self._port_start = port_start
        self._supervisors = []
        self._connections = []
        self._robot_queue = asyncio.Queue()
        self._free_simulator = [True for _ in range(n_cores)]
        self._workers = []

    async def _start_debug(self):
        connection = await World.create(self._settings, world_address=("127.0.0.1", self._port_start))
        self._connections.append(connection)
        self._workers.append(asyncio.create_task(self._simulator_queue_worker(0)))

    async def start(self):
        if self._settings.simulator_cmd == 'debug':
            await self._start_debug()
            return
        future_launches = []
        future_connections = []
        for i in range(self._n_cores):
            simulator_supervisor = DynamicSimSupervisor(
                world_file=self._settings.world,
                simulator_cmd=self._settings.simulator_cmd,
                simulator_args=["--verbose"],
                plugins_dir_path=os.path.join('.', 'build', 'lib'),
                models_dir_path=os.path.join('.', 'models'),
                simulator_name='gazebo_{}'.format(i)
            )
            simulator_future_launch = simulator_supervisor.launch_simulator(port=self._port_start+i)

            future_launches.append(simulator_future_launch)
            self._supervisors.append(simulator_supervisor)

        await asyncio.sleep(5)

        for i, future_launch in enumerate(future_launches):
            await future_launch
            connection_future = World.create(self._settings, world_address=("127.0.0.1", self._port_start+i))
            future_connections.append(connection_future)

        for i, future_conn in enumerate(future_connections):
            self._connections.append(await future_conn)
            self._workers.append(asyncio.create_task(self._simulator_queue_worker(i)))

        await asyncio.sleep(1)

    def test_robot(self, robot, conf: PopulationConfig):
        """
        :param robot: robot phenotype
        :param conf: configuration of the experiment
        :return:
        """
        future = asyncio.Future()
        self._robot_queue.put_nowait((robot, future, conf))
        return future

    async def _restart_simulator(self, i):
        # restart simulator
        address = 'localhost'
        port = self._port_start+i
        logger.error("Restarting simulator")
        self._connections[i].disconnect()
        await (await self._supervisors[i].relaunch(10, address=address, port=port))
        await asyncio.sleep(5)
        self._connections[i] = await World.create(self._settings, world_address=(address, port))

    async def _worker_evaluate_robot(self, connection, robot, future, conf):
        await asyncio.sleep(0.01)
        start = time.time()
        evaluation_future = asyncio.create_task(self._evaluate_robot(connection, robot, conf))
        while not evaluation_future.done():
            elapsed = time.time()-start
            # WAITED TO MUCH, RESTART SIMULATOR
            if elapsed > 120:
                logger.error(f"Simulator restarted after {elapsed}")
                return False
            await asyncio.sleep(0.2)

        elapsed = time.time()-start
        logger.info(f"time taken to do a simulation {elapsed}")

        exception = evaluation_future.exception()
        if exception is not None:
            logger.exception(f"Exception running robot {robot.phenotype}", exc_info=exception)
            return False

        robot_fitness = await evaluation_future
        future.set_result(robot_fitness)

        return True

    async def _simulator_queue_worker(self, i):
        self._free_simulator[i] = True
        while True:
            logger.info(f"simulator {i} waiting for robot")
            (robot, future, conf) = await self._robot_queue.get()
            self._free_simulator[i] = False
            logger.info(f"Picking up robot {robot.phenotype.id} into simulator {i}")
            success = await self._worker_evaluate_robot(self._connections[i], robot, future, conf)
            if success:
                if robot.failed_eval_attempt_count == 3:
                    logger.info("Robot failed to be evaluated 3 times. Saving robot to failed_eval file")
                    conf.experiment_management.export_failed_eval_robot(robot)
                robot.failed_eval_attempt_count = 0
                logger.info(f"simulator {i} finished robot {robot.phenotype.id}")
            else:
                # restart of the simulator happened
                robot.failed_eval_attempt_count += 1
                logger.info(f"Robot {robot.phenotype.id} current failed attempt: {robot.failed_eval_attempt_count}")
                await self._robot_queue.put((robot, future, conf))
                await self._restart_simulator(i)
            self._robot_queue.task_done()
            self._free_simulator[i] = True

    async def _evaluate_robot(self, simulator_connection, robot, conf):
        if robot.failed_eval_attempt_count == 3:
            logger.info(f'Robot {robot.phenotype.id} evaluation failed (reached max attempt of 3), fitness set to None.')
            robot_fitness = None
        else:
            await simulator_connection.pause(True)
            insert_future = await simulator_connection.insert_robot(robot.phenotype, Vector3(0, 0, self._settings.z_start))
            robot_manager = await insert_future
            await simulator_connection.pause(False)
            start = time.time()
            # Start a run loop to do some stuff
            max_age = conf.evaluation_time
            while robot_manager.age() < max_age:
                await asyncio.sleep(1.0 / 5)  # 5= state_update_frequency
            end = time.time()
            elapsed = end-start
            logger.info(f'Time taken: {elapsed}')

            robot_fitness = conf.fitness_function(robot_manager, robot)

            measures_list = {'displacement_velocity_hill': measures.displacement_velocity_hill(robot_manager),
                             'head_balance': measures.head_balance(robot_manager),
                             'contacts': measures.contacts(robot_manager, robot),
                             'displacement_velocity': measures.displacement_velocity(robot_manager)
                             }
            conf.experiment_management.export_behavior_measures(robot.phenotype.id, measures_list)

            delete_future = await simulator_connection.delete_all_robots()
        # delete_future = await simulator_connection.delete_robot(robot_manager)
            await delete_future
            await simulator_connection.pause(True)
            await simulator_connection.reset(rall=True, time_only=True, model_only=False)
        return robot_fitness


    async def _joint(self):
        await self._robot_queue.join()

