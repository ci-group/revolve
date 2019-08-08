#!/usr/bin/env python3
import asyncio
import os
import sys
import random
import logging
import yaml
import enum
import time
import shutil
import pickle

from pyrevolve.custom_logging import logger
from pyrevolve import parser
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import World
from pyrevolve.tol.manage import measures
from pyrevolve.evolution import fitness
from pyrevolve.evolution.individual import Individual
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.revolve_bot.brain import BrainRLPowerSplines
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor

ROBOT_BATTERY = 5000
ROBOT_STOP = 5050
ROBOT_SELF_COLLIDE = False
REPRODUCE_LOCALLY = True
REPRODUCE_LOCALLY_RADIUS = 2
INDIVIDUAL_MAX_AGE = 60 * 2  # 2 minutes
INDIVIDUAL_MAX_AGE_SIGMA = 1.0
SEED_POPULATION_START = 50
MIN_POP = 20
MAX_POP = 50
Z_SPAWN_DISTANCE = 0.2
LIMIT_X = 3
LIMIT_Y = 3
MATURE_AGE = 5
MATE_DISTANCE = 0.6
MATING_COOLDOWN = 0.1
COUPLE_MATING_LIMIT = 1
MATING_INCREASE_RATE = 1.0
SNAPSHOT_TIME = 60 * 10  # 10 minutes
RECENT_CHILDREN_DELTA_TIME = 30

PLASTICODING_CONF = PlasticodingConfig(
    max_structural_modules=20
)
CROSSOVER_CONF = CrossoverConfig(crossover_prob=1.0)
MUTATION_CONF = MutationConfig(mutation_prob=0.8, genotype_conf=PLASTICODING_CONF)

# FOLDER WHERE TO SAVE THE EXPERIMENT
# {current_folder}/data/{arguments.experiment_name}
# example ~/projects/revolve/experiments/unmanaged/data/default_experiment
DATA_FOLDER_BASE = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data',
)


def make_folders(base_dirpath):
    if os.path.exists(base_dirpath):
        assert(os.path.isdir(base_dirpath))
    else:
        os.makedirs(base_dirpath)

    counter = 0
    while True:
        dirpath = os.path.join(base_dirpath, str(counter))
        if not os.path.exists(dirpath):
            break
        counter += 1

    print(f"CHOSEN EXPERIMENT FOLDER {dirpath}")

    # if os.path.exists(dirpath):
    #     shutil.rmtree(dirpath)
    os.mkdir(dirpath)
    os.mkdir(os.path.join(dirpath, 'genotypes'))
    os.mkdir(os.path.join(dirpath, 'phenotypes'))
    os.mkdir(os.path.join(dirpath, 'descriptors'))

    return dirpath


class OnlineIndividual(Individual):
    class BirthType(enum.Enum):
        NEW = 0
        MATE = 1

    def __init__(self, genotype, max_age=None, parents=None):
        super().__init__(genotype)
        self.parents = parents
        if self.parents is None:
            self.birth_type = OnlineIndividual.BirthType.NEW
        else:
            self.birth_type = OnlineIndividual.BirthType.MATE
        self.children = []
        self.manager = None
        self.max_age = random.gauss(INDIVIDUAL_MAX_AGE, INDIVIDUAL_MAX_AGE_SIGMA) if max_age is None else max_age

    @staticmethod
    def clone_from(other):
        self = OnlineIndividual(other.genotype, other.max_age)
        self.phenotype = other.phenotype
        self.manager = other.manager
        self.fitness = other.fitness
        self.parents = other.parents

    def develop(self):
        super().develop()
        # self.phenotype._brain = BrainRLPowerSplines(evaluation_rate=10.0)

    def age(self):
        if self.manager is not None:
            return self.manager.age()
        else:
            return 0.0

    def charge(self):
        if self.manager is not None:
            return self.manager.charge()
        else:
            return 0.0

    def pos(self):
        if self.manager is not None:
            return self.manager.last_position
        else:
            return None

    def alive(self):
        if self.manager is not None:
            return not self.manager.dead
        else:
            return None

    def starting_position(self):
        if self.manager is not None:
            return self.manager.starting_position
        else:
            return None

    @property
    def name(self):
        return self.id

    def distance_to(self, other, planar: bool = True):
        """
        Calculates the Euclidean distance from this robot to
        the given vector position.
        :param other: Target for measuring distance
        :type other: Vector3|OnlineIndividual
        :param planar: If true, only x/y coordinates are considered.
        :return: distance to other
        :rtype: float
        """
        my_pos = self.pos()
        other_pos = other if isinstance(other, Vector3) else other.pos()

        diff = my_pos - other_pos
        if planar:
            diff.z = 0

        return diff.norm()

    def mature(self):
        return self.age() > MATURE_AGE

    def _wants_to_mate(self, other, mating_multiplier):
        if not self.mature():
            return False

        if self.distance_to(other) > MATE_DISTANCE * mating_multiplier:
            return False

        if self.manager.last_mate is not None and \
                float(self.manager.last_update - self.manager.last_mate) < MATING_COOLDOWN:
            return False

        mate_count = self.manager.mated_with.get(other.manager.name, 0)
        if mate_count > COUPLE_MATING_LIMIT:
            return False

        return True

    def mate(self, other, mating_distance_multiplier: float):
        """
        Will try to mate with other
        :param other: potential mate
        :type other: OnlineIndividual
        :param mating_distance_multiplier: multiplier for mating distance, default should be 1
        :return: Genotype generated by the mating process, None if no mating happened
        :rtype: Genotype|None
        """
        if not (self._wants_to_mate(other, mating_distance_multiplier)
                and other._wants_to_mate(self, mating_distance_multiplier)):
            return None

        # save the mating
        self.manager.last_mate = self.manager.last_update
        if other.manager.name in self.manager.mated_with:
            self.manager.mated_with[other.manager.name] += 1
        else:
            self.manager.mated_with[other.manager.name] = 1

        genotype = standard_crossover([self, other], PLASTICODING_CONF, CROSSOVER_CONF)
        genotype = standard_mutation(genotype, MUTATION_CONF)

        child = OnlineIndividual(genotype)

        self.children.append(child)
        other.children.append(child)
        return child

    def export_life_data(self, folder):
        life_measures = {
            'distance': str(measures.displacement(self.manager)[0]),
            'distance_magnitude': str(measures.displacement(self.manager)[0].magnitude()),
            'velocity': str(measures.velocity(self.manager)),
            'displacement_velocity': str(measures.displacement_velocity(self.manager)),
            'path_length': str(measures.path_length(self.manager)),
        }

        life = {
            'starting_time': float(self.manager.starting_time),
            'age': float(self.age()),
            'charge': self.charge(),
            'start_pos': str(self.starting_position()),
            'last_pos': str(self.pos()),
            'avg_orientation': str(Vector3(self.manager.avg_roll, self.manager.avg_pitch, self.manager.avg_yaw)),
            'avg_pos': str(Vector3(self.manager.avg_x, self.manager.avg_y, self.manager.avg_z)),
            'last_mate': str(self.manager.last_mate),
            'alive': str(self.alive()),
            'birth': str(self.birth_type),
            'parents': [parent.name for parent in self.parents] if self.parents is not None else 'None',
            'children': [child.name for child in self.children],
            'measures': life_measures,
        }

        with open(os.path.join(folder, f'life_{self.id}.yaml'), 'w') as f:
            f.write(str(yaml.dump(life)))

    def snapshot_data(self):
        return {
            'genotype': self.genotype,
            'parents': self.parents,
            'children': self.children,
            'birth': self.birth_type,
            'last_mate': self.manager.last_mate,
            'start_pos': self.starting_position(),
            'starting_time': self.manager.starting_time
        }

    def export(self, folder):
        self.export_genotype(folder)
        self.export_phenotype(folder)
        self.export_life_data(folder)

    def __repr__(self):
        return f'Individual_{self.id}({self.age()}, {self.charge()}, {self.pos()})'


def random_spawn_pos():
    return Vector3(
        random.uniform(-LIMIT_X, LIMIT_X),
        random.uniform(-LIMIT_Y, LIMIT_Y),
        Z_SPAWN_DISTANCE
    )


def random_uniform_unit_vec():
    return Vector3(
        random.uniform(-1, 1),
        random.uniform(-1, 1),
        Z_SPAWN_DISTANCE
    ).normalized()


class Finish(Exception):
    pass


class Population(object):
    def __init__(self, log, data_folder, connection):
        self._log = log
        self._data_folder = data_folder
        self._connection = connection
        self._robots = []
        self._robot_id_counter = 0
        self._mating_multiplier = 1.0
        self._mating_increase_rate = MATING_INCREASE_RATE
        self._recent_children = []
        self._recent_children_start_time = -1.0
        self._recent_children_delta_time = RECENT_CHILDREN_DELTA_TIME

    def __len__(self):
        return len(self._robots)

    async def _insert_robot(self, robot, pos: Vector3, life_duration: float):
        robot.update_substrate()
        robot.self_collide = ROBOT_SELF_COLLIDE
        robot.battery_level = ROBOT_BATTERY

        # Insert the robot in the simulator
        robot_manager = await asyncio.wait_for(self._connection.insert_robot(robot, pos, life_duration), 5)
        return robot_manager

    async def _insert_individual(self, individual: OnlineIndividual, pos: Vector3):
        individual.develop()
        individual.manager = await self._insert_robot(individual.phenotype, pos, individual.max_age)
        individual.export(self._data_folder)
        return individual

    async def _remove_individual(self, individual: OnlineIndividual):
        self._robots.remove(individual)
        individual.export(self._data_folder)

        self._connection.unregister_robot(individual.manager)
        # await self._connection.delete_robot(individual.manager)
        if individual.id == f'robot_{ROBOT_STOP}':
            raise Finish()

    def _is_pos_occupied(self, pos, distance):
        for robot in self._robots:
            if robot.distance_to(pos) < distance:
                return True
        return False

    class NoPositionFound(Exception):
        def __str__(self):
            return "NoPositionFound"

    def _free_random_spawn_pos(self, distance=MATE_DISTANCE + 0.1, n_tries=100):
        pos = random_spawn_pos()
        i = 1
        while self._is_pos_occupied(pos, distance):
            i += 1
            if i > n_tries:
                raise self.NoPositionFound()
            pos = random_spawn_pos()
        return pos

    def _free_random_spawn_pos_area(self, center: Vector3, radius: float=REPRODUCE_LOCALLY_RADIUS, distance=MATE_DISTANCE + 0.1, n_tries=100):
        pos = center + (random_uniform_unit_vec() * random.uniform(0,radius))
        i = 1
        while self._is_pos_occupied(pos, distance):
            i += 1
            if i > n_tries:
                raise self.NoPositionFound()
            pos = center + (random_uniform_unit_vec() * random.uniform(0,radius))
        return pos

    async def _generate_insert_random_robot(self, _id: int):
        # Load a robot from yaml
        genotype = random_initialization(PLASTICODING_CONF, _id)
        individual = OnlineIndividual(genotype)
        return await self._insert_individual(individual, self._free_random_spawn_pos())

    async def seed_initial_population(self, pause_while_inserting: bool):
        """
        Seed a new population
        """
        if pause_while_inserting:
            await self.pause(True)
        await self._connection.reset(rall=True, time_only=True, model_only=False)
        await self.immigration_season(SEED_POPULATION_START)
        if pause_while_inserting:
            await self.pause(False)

    def print_population(self):
        for individual in self._robots:
            self._log.info(f"{individual} "
                           f"battery {individual.manager.charge()} "
                           f"age {individual.manager.age()} "
                           f"fitness is {fitness.online_old_revolve(individual.manager)}")

    async def death_season(self):
        """
        Checks for age in the all population and if it's their time of that (currently based on age)
        """
        for individual in self._robots:
            # alive can be None or boolean
            alive = individual.alive()
            if alive is False or individual.age() > individual.max_age:
                self._log.debug(f"Attempting ROBOT DIES OF OLD AGE: {individual} - total_population: {len(self._robots)}")
                await self._remove_individual(individual)
                self._log.info(f"ROBOT DIES OF OLD AGE: {individual} - total_population: {len(self._robots)}")

    async def immigration_season(self, population_minimum=MIN_POP):
        """
        Generates new random individual that are inserted in our population if the population size is too little
        """
        while len(self._robots) < population_minimum:
            self._robot_id_counter += 1
            self._log.debug(f"Attempting LOW REACHED")
            try:
                individual = await self._generate_insert_random_robot(self._robot_id_counter)
                self._log.info(f"LOW REACHED: inserting new random robot: {individual}")
                self._robots.append(individual)
            except (Population.NoPositionFound, asyncio.TimeoutError) as e:
                self._log.error(f"LOW REACHED failed: {e}")

    def adjust_mating_multiplier(self, time):
        if self._recent_children_start_time < 0:
            self._recent_children_start_time = time
            return

        if time - self._recent_children_start_time > self._recent_children_delta_time:
            # Time to update the multiplier!
            self._recent_children_start_time = time
            n = len(self._recent_children)
            if n < 3:
                self._mating_multiplier *= self._mating_increase_rate
                self._log.info(f'NOT ENOUGH CHILDREN, increasing the range to {MATE_DISTANCE * self._mating_multiplier}'
                               f' (multiplier: {self._mating_multiplier})')
            elif n > 10:
                self._mating_multiplier /= self._mating_increase_rate
                self._log.info(f'TOO MANY CHILDREN,   decreasing the range to {MATE_DISTANCE * self._mating_multiplier}'
                               f' (multiplier: {self._mating_multiplier})')

            self._recent_children.clear()

    async def mating_season(self):
        """
        Checks if mating condition are met for all couple of robots. If so, it produces a new robot from crossover.
        That robot is inserted into the population.
        """

        class BreakIt(Exception):
            pass

        try:
            if len(self._robots) > MAX_POP:
                raise BreakIt
            for individual1 in self._robots:
                if not individual1.mature():
                    continue
                for individual2 in self._robots:
                    if len(self._robots) > MAX_POP:
                        raise BreakIt
                    if individual1 is individual2:
                        continue

                    individual3 = individual1.mate(individual2, mating_distance_multiplier=self._mating_multiplier)
                    if individual3 is None:
                        continue

                    self._recent_children.append(individual3)

                    self._robot_id_counter += 1
                    individual3.genotype.id = self._robot_id_counter

                    # pos3 = (individual1.pos() + individual2.pos())/2
                    # pos3.z = Z_SPAWN_DISTANCE
                    try:
                        if REPRODUCE_LOCALLY:
                            pos3 = (individual1.pos() + individual2.pos())/2
                            pos3 = self._free_random_spawn_pos_area(pos3)
                        else:
                            pos3 = self._free_random_spawn_pos()
                        self._log.debug(
                            f'Attempting mate between {individual1} and {individual2} generated {individual3} POP({len(self._robots)})')
                        await self._insert_individual(individual3, pos3)
                        self._log.info(
                            f'MATE!!!! between {individual1} and {individual2} generated {individual3} POP({len(self._robots)})')
                    except Population.NoPositionFound:
                        self._log.info('Space is too crowded! Cannot insert the new individual, giving up.')
                    except asyncio.TimeoutError:
                        self._log.info(
                            f'MATE failed!!!! between {individual1} and {individual2} generated {individual3} POP({len(self._robots)})')
                    else:
                        self._robots.append(individual3)

        except BreakIt:
            pass

    async def pause(self, pause, how_many_times=20):
        counter = 0
        while True:
            try:
                await asyncio.wait_for(self._connection.pause(pause), 0.2)
                return
            except asyncio.TimeoutError:
                counter += 1
                if counter > how_many_times:
                    raise

    async def create_snapshot(self):
        await self.pause(True)
        await asyncio.sleep(0.05)
        snapshot_folder = await self._connection.create_snapshot(pause_when_saving=False)

        population_snapshot_data = {
            # 'log': self._log,
            'data_folder': self._data_folder,
            # 'connection': self._connection,
            'robots': [],
            'robot_id_counter': self._robot_id_counter,
            'mating_multiplier': self._mating_multiplier,
            'mating_increase_rate': self._mating_increase_rate,
            'recent_children': [r.name for r in self._recent_children],
            'recent_children_start_time': self._recent_children_start_time,
            'recent_children_delta_time': self._recent_children_delta_time,
        }

        for robot in self._robots:
            population_snapshot_data['robots'].append(robot.snapshot_data())

        sys.setrecursionlimit(10000)
        with open(os.path.join(snapshot_folder, 'online_population.pickle'), 'wb') as f:
            pickle.dump(population_snapshot_data, f, protocol=-1)

        await self.pause(False)


async def run():
    # Parse command line / file input arguments
    settings = parser.parse_args()

    # create ata folder and logger
    data_folder = os.path.join(DATA_FOLDER_BASE, settings.experiment_name)
    data_folder = make_folders(data_folder)
    log = logger.create_logger('experiment', handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(data_folder, 'experiment_manager.log'), mode='w')
    ])

    # Set debug level to DEBUG
    log.setLevel(logging.DEBUG)

    # Save settings
    experimental_settings = {
        'START': {
            'human': time.strftime("%a, %d %b %Y %H:%M:%S"),
            'seconds': time.time(),
        },
        'ROBOT_BATTERY': ROBOT_BATTERY,
        'ROBOT_STOP': ROBOT_STOP,
        'ROBOT_SELF_COLLIDE': ROBOT_SELF_COLLIDE,
        'REPRODUCE_LOCALLY_RADIUS': REPRODUCE_LOCALLY_RADIUS,
        'INDIVIDUAL_MAX_AGE': INDIVIDUAL_MAX_AGE,
        'INDIVIDUAL_MAX_AGE_SIGMA': INDIVIDUAL_MAX_AGE_SIGMA,
        'SEED_POPULATION_START': SEED_POPULATION_START,
        'MIN_POP': MIN_POP,
        'MAX_POP': MAX_POP,
        'Z_SPAWN_DISTANCE': Z_SPAWN_DISTANCE,
        'LIMIT_X': LIMIT_X,
        'LIMIT_Y': LIMIT_Y,
        'MATURE_AGE': MATURE_AGE,
        'MATE_DISTANCE': MATE_DISTANCE,
        'MATING_COOLDOWN': MATING_COOLDOWN,
        'COUPLE_MATING_LIMIT': COUPLE_MATING_LIMIT,
        'MATING_INCREASE_RATE': MATING_INCREASE_RATE,
        'RECENT_CHILDREN_DELTA_TIME': RECENT_CHILDREN_DELTA_TIME,

        'PLASTICODING_CONF.max_structural_modules': PLASTICODING_CONF.max_structural_modules,
        'CROSSOVER_PROBABILITY': CROSSOVER_CONF.crossover_prob,
        'MUTATION_PROBABILITY': MUTATION_CONF.mutation_prob,

        # FOLDER WHERE TO SAVE THE EXPERIMENT
        # {current_folder}/data/{arguments.experiment_name}
        # example ~/projects/revolve/experiments/unmanaged/data/default_experiment
        'DATA_FOLDER_BASE': DATA_FOLDER_BASE,
    }
    with open(os.path.join(data_folder, 'experimental_settings.yaml'), 'w') as f:
        f.write(str(yaml.dump(experimental_settings)))

    # Start Simulator
    if settings.simulator_cmd != 'debug':
        def simulator_dead(_process, ret_code):
            log.error("SIMULATOR DIED BEFORE THE END OF THE EXPERIMENT")
            sys.exit(ret_code)

        simulator_supervisor = DynamicSimSupervisor(
            world_file=settings.world,
            simulator_cmd=settings.simulator_cmd,
            simulator_args=["--verbose"],
            plugins_dir_path=os.path.join('.', 'build', 'lib'),
            models_dir_path=os.path.join('.', 'models'),
            simulator_name='gazebo',
            process_terminated_callback=simulator_dead,
        )
        await simulator_supervisor.launch_simulator(port=settings.port_start)
        # let there be some time to sync all initial output of the simulator
        await asyncio.sleep(5)

    # Connect to the simulator and pause
    connection = await World.create(settings, world_address=('127.0.0.1', settings.port_start))
    connection.output_directory = os.path.join(data_folder, 'snapshots')
    await asyncio.sleep(1)

    robot_population = Population(log, data_folder, connection)

    log.info("SEEDING POPULATION STARTED")
    await robot_population.seed_initial_population(pause_while_inserting=False)
    log.info("SEEDING POPULATION FINISHED")

    # Start the main life loop
    try:
        last_snapshot = connection.last_time

        log.info("creating initial snapshot")
        success = await robot_population.create_snapshot()

        while True:
            world_time = connection.last_time
            if float(world_time - last_snapshot) > SNAPSHOT_TIME:
                log.info(f"Creating snapshot at {world_time}")
                last_snapshot = world_time
                success = await robot_population.create_snapshot()
            await robot_population.death_season()
            await robot_population.mating_season()
            await robot_population.immigration_season()
            robot_population.adjust_mating_multiplier(connection.age())

            await asyncio.sleep(0.05)
    except Finish:
        await asyncio.wait_for(connection.disconnect(), 10)
        if settings.simulator_cmd != 'debug':
            await asyncio.wait_for(simulator_supervisor.stop(), 10)
        log.info("EVOLUTION finished successfully")
