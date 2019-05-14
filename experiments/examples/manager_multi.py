#!/usr/bin/env python3
import os
import sys
import asyncio
import time

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
relative = os.path.join(current_dir,__file__)
sys.path.append(newpath)

from pygazebo.pygazebo import DisconnectError

from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.SDF.math import Vector3
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.custom_logging.logger import logger


class ExperimentConfig:
    def __init__(self):

        self.num_generations = 100

        self.genotype_conf = PlasticodingConfig(
            max_structural_modules=20,
        )
        self.mutation_conf = MutationConfig(
            mutation_prob=0.8,
            genotype_conf=self.genotype_conf,
        )

        self.crossover_conf = CrossoverConfig(
            crossover_prob=0.8,
        )

        self.population_conf = PopulationConfig(
            population_size=100,
            genotype_constructor=random_initialization,
            genotype_conf=self.genotype_conf,
            fitness_function=fitness.online_old_revolve,
            mutation_operator=standard_mutation,
            mutation_conf=self.mutation_conf,
            crossover_operator=standard_crossover,
            crossover_conf=self.crossover_conf,
            selection=lambda individuals: tournament_selection(individuals, 2),
            parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
            population_management=steady_state_population_management,
            population_management_selector=tournament_selection,
            evaluation_time=30,
            offspring_size=20,
        )


class SimulatorQueue:
    def __init__(self, n_cores: int, settings):
        assert (n_cores > 0)
        self._settings = settings
        self._n_cores = n_cores
        self._supervisors = []
        self._connections = []
        self._robot_queue = asyncio.Queue()
        self._free_simulator = [True for _ in range(n_cores)]
        self._workers = []

    async def start(self):
        future_launches = []
        future_connections = []
        for i in range(self._n_cores):
            simulator_supervisor = DynamicSimSupervisor(
                world_file=newpath + "/" + self._settings.world,
                simulator_cmd=self._settings.simulator_cmd,
                simulator_args=["--verbose"],
                plugins_dir_path=os.path.join(newpath, 'build', 'lib'),
                models_dir_path=os.path.join(newpath, 'models'),
                simulator_name='gazebo_{}'.format(i)
            )
            simulator_future_launch = simulator_supervisor.launch_simulator(port=11345+i)

            future_launches.append(simulator_future_launch)
            self._supervisors.append(simulator_supervisor)

        for i, future_launch in enumerate(future_launches):
            await future_launch
            connection_future = World.create(self._settings, world_address=("127.0.0.1", 11345+i))
            future_connections.append(connection_future)

        for i, future_conn in enumerate(future_connections):
            self._connections.append(await future_conn)
            self._workers.append(asyncio.create_task(self._simulator_queue_worker(i)))

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
        logger.error("Restarting simulator")
        self._connections[i].disconnect()
        await (await self._supervisors[i].relaunch(5))
        await asyncio.sleep(5)
        self._connections[i] = await World.create(self._settings, world_address=("127.0.0.1", 11345+i))

    async def _simulator_queue_worker(self, i):
        self._free_simulator[i] = True
        while True:
            logger.info(f"simulator {i} waiting for robot")
            (robot, future, conf) = await self._robot_queue.get()
            logger.info(f"Picking up robot {robot.id} into simulator {i}")
            self._free_simulator[i] = False

            start = time.time()
            evaluation_future = asyncio.create_task(self._evaluate_robot(self._connections[i], robot, conf))
            broken = False
            while not evaluation_future.done():
                elapsed = time.time()-start
                if elapsed > 5:
                    await self._robot_queue.put((robot, future, conf))
                    await self._restart_simulator(i)
                    broken = True
                    break
                await asyncio.sleep(0.1)

            if not broken:
                await evaluation_future
                robot_fitness = evaluation_future.result()

                future.set_result(robot_fitness)

            self._robot_queue.task_done()
            self._free_simulator[i] = True
            logger.info(f"simulator {i} finished robot {robot.id}")

    @staticmethod
    async def _evaluate_robot(simulator_connection, robot, conf):
        await simulator_connection.pause(True)
        insert_future = await simulator_connection.insert_robot(robot, Vector3(0, 0, 0.25))
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

        robot_fitness = conf.fitness_function(robot_manager)
        await simulator_connection.pause(True)
        delete_future = await simulator_connection.delete_all_robots()  # robot_manager
        await delete_future
        return robot_fitness

    async def _joint(self):
        await self._robot_queue.join()


async def run():
    """
    The main coroutine, which is started below.
    """

    n_cores = 1

    experiment_conf = ExperimentConfig()
    settings = parser.parse_args()
    queue = SimulatorQueue(n_cores, settings)
    await queue.start()

    population = Population(experiment_conf.population_conf)
    await population.init_pop(queue)
    # population.simulator_connection.disconnect()

    # await simulator_supervisor.relaunch()

    gen_num = 0
    while gen_num < experiment_conf.num_generations:
        population = await population.next_gen(gen_num+1, queue)
        # simulator_connection.disconnect()
        # simulator_supervisor.relaunch()
        # population.simulator_connection = await World.create(settings)
        gen_num += 1

    # output result after completing all generations...
    # simulator_supervisor.stop()


def main():
    import traceback

    def handler(_loop, context):
        try:
            exc = context['exception']
        except KeyError:
            print(context['message'])
            return

        if isinstance(exc, DisconnectError) \
                or isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            # sys.exit(0)

        if isinstance(exc, OSError) and exc.errno == 9:
            print(exc)
            traceback.print_exc()
            return

        traceback.print_exc()
        raise exc

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handler)
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Got CtrlC, shutting down.")


if __name__ == '__main__':
    print("STARTING")
    main()
    print("FINISHED")
