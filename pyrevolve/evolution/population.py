import asyncio
import math
import os
import random
import sys
from typing import Tuple

from pyrevolve.angle.manage.robotmanager import RobotManager
from pyrevolve.evolution.individual import Individual
from pyrevolve.revolve_bot.brain.cpg_target import BrainCPGTarget
from pyrevolve.revolve_bot.revolve_bot import RevolveBot
from pyrevolve.tol.manage import measures
from pyrevolve.tol.manage.measures import BehaviouralMeasurements

from ..custom_logging.logger import logger


class PopulationConfig:
    def __init__(
        self,
        population_size: int,
        genotype_constructor,
        genotype_conf,
        fitness_function,
        mutation_operator,
        mutation_conf,
        crossover_operator,
        crossover_conf,
        selection,
        parent_selection,
        population_management,
        population_management_selector,
        evaluation_time,
        experiment_name,
        experiment_management,
        offspring_size=None,
        next_robot_id=1,
        grace_time: float = 0.0,
    ):
        """
        Creates a PopulationConfig object that sets the particular configuration for the population

        :param population_size: size of the population
        :param genotype_constructor: class of the genotype used
        :param genotype_conf: configuration for genotype constructor
        :param fitness_function: function that takes in a `RobotManager` as a parameter and produces a fitness for the robot
        :param mutation_operator: operator to be used in mutation
        :param mutation_conf: configuration for mutation operator
        :param crossover_operator: operator to be used in crossover
        :param selection: selection type
        :param parent_selection: selection type during parent selection
        :param population_management: type of population management ie. steady state or generational
        :param evaluation_time: duration of an experiment
        :param experiment_name: name for the folder of the current experiment
        :param experiment_management: object with methods for managing the current experiment
        :param offspring_size (optional): size of offspring (for steady state)
        """
        self.population_size = population_size
        self.genotype_constructor = genotype_constructor
        self.genotype_conf = genotype_conf
        self.fitness_function = fitness_function
        self.mutation_operator = mutation_operator
        self.mutation_conf = mutation_conf
        self.crossover_operator = crossover_operator
        self.crossover_conf = crossover_conf
        self.parent_selection = parent_selection
        self.selection = selection
        self.population_management = population_management
        self.population_management_selector = population_management_selector
        self.evaluation_time = evaluation_time
        self.experiment_name = experiment_name
        self.experiment_management = experiment_management
        self.offspring_size = offspring_size
        self.next_robot_id = next_robot_id
        self.grace_time: float = grace_time


class Population:
    def __init__(
        self,
        conf: PopulationConfig,
        simulator_queue,
        analyzer_queue=None,
        next_robot_id=1,
    ):
        """
        Creates a Population object that initialises the
        individuals in the population with an empty list
        and stores the configuration of the system to the
        conf variable.

        :param conf: configuration of the system
        :param simulator_queue: connection to the simulator queue
        :param analyzer_queue: connection to the analyzer simulator queue
        :param next_robot_id: (sequential) id of the next individual to be created
        """
        self.conf = conf
        self.individuals = []
        self.analyzer_queue = analyzer_queue
        self.simulator_queue = simulator_queue
        self.next_robot_id = next_robot_id

    def _new_individual(self, genotype):
        individual = Individual(genotype)
        individual.develop()
        self.conf.experiment_management.export_genotype(individual)
        self.conf.experiment_management.export_phenotype(individual)
        self.conf.experiment_management.export_phenotype_images(
            os.path.join("data_fullevolution", "phenotype_images"), individual
        )
        individual.phenotype.measure_phenotype()
        individual.phenotype.export_phenotype_measurements(
            self.conf.experiment_management.data_folder
        )

        return individual

    async def load_individual(self, id):
        data_path = self.conf.experiment_management.data_folder
        genotype = self.conf.genotype_constructor(self.conf.genotype_conf, id)
        genotype.load_genotype(
            os.path.join(data_path, "genotypes", f"genotype_{id}.txt")
        )

        individual = Individual(genotype)
        individual.develop()
        individual.phenotype.measure_phenotype()

        with open(os.path.join(data_path, "fitness", f"fitness_{id}.txt")) as f:
            data = f.readlines()[0]
            individual.fitness = None if data == "None" else float(data)

        with open(
            os.path.join(data_path, "descriptors", f"behavior_desc_{id}.txt")
        ) as f:
            lines = f.readlines()
            if lines[0] == "None":
                individual.phenotype._behavioural_measurements = None
            else:
                individual.phenotype._behavioural_measurements = (
                    measures.BehaviouralMeasurements()
                )
                for line in lines:
                    if line.split(" ")[0] == "velocity":
                        individual.phenotype._behavioural_measurements.velocity = float(
                            line.split(" ")[1]
                        )
                    # if line.split(' ')[0] == 'displacement':
                    #   individual.phenotype._behavioural_measurements.displacement = float(line.split(' ')[1])
                    if line.split(" ")[0] == "displacement_velocity":
                        individual.phenotype._behavioural_measurements.displacement_velocity = float(
                            line.split(" ")[1]
                        )
                    if line.split(" ")[0] == "displacement_velocity_hill":
                        individual.phenotype._behavioural_measurements.displacement_velocity_hill = float(
                            line.split(" ")[1]
                        )
                    if line.split(" ")[0] == "head_balance":
                        individual.phenotype._behavioural_measurements.head_balance = (
                            float(line.split(" ")[1])
                        )
                    if line.split(" ")[0] == "contacts":
                        individual.phenotype._behavioural_measurements.contacts = float(
                            line.split(" ")[1]
                        )

        return individual

    async def load_snapshot(self, gen_num):
        """
        Recovers all genotypes and fitnesses of robots in the lastest selected population
        :param gen_num: number of the generation snapshot to recover
        """
        data_path = self.conf.experiment_management.experiment_folder
        for r, d, f in os.walk(data_path + "/selectedpop_" + str(gen_num)):
            for file in f:
                if "body" in file:
                    id = (
                        file.split(".")[0].split("_")[-2]
                        + "_"
                        + file.split(".")[0].split("_")[-1]
                    )
                    self.individuals.append(await self.load_individual(id))

    async def load_offspring(
        self, last_snapshot, population_size, offspring_size, next_robot_id
    ):
        """
        Recovers the part of an unfinished offspring
        :param
        :return:
        """
        individuals = []
        # number of robots expected until the latest snapshot
        if last_snapshot == -1:
            n_robots = 0
        else:
            n_robots = population_size + last_snapshot * offspring_size

        for robot_id in range(n_robots + 1, next_robot_id):
            individuals.append(await self.load_individual("robot_" + str(robot_id)))

        self.next_robot_id = next_robot_id
        return individuals

    async def init_pop(self, recovered_individuals=[]):
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        for i in range(self.conf.population_size - len(recovered_individuals)):
            individual = self._new_individual(
                self.conf.genotype_constructor(
                    self.conf.genotype_conf, self.next_robot_id
                )
            )
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)
        self.individuals = recovered_individuals + self.individuals

    async def next_gen(self, gen_num, recovered_individuals=[]):
        """
        Creates next generation of the population through selection, mutation, crossover

        :param gen_num: generation number
        :param individuals: recovered offspring
        :return: new population
        """

        new_individuals = []

        for _i in range(self.conf.offspring_size - len(recovered_individuals)):
            # Selection operator (based on fitness)
            # Crossover
            if self.conf.crossover_operator is not None:
                parents = self.conf.parent_selection(self.individuals)
                child_genotype = self.conf.crossover_operator(
                    parents, self.conf.genotype_conf, self.conf.crossover_conf
                )
                child = Individual(child_genotype)
            else:
                child = self.conf.selection(self.individuals)

            child.genotype.id = self.next_robot_id
            self.next_robot_id += 1

            # Mutation operator
            child_genotype = self.conf.mutation_operator(
                child.genotype, self.conf.mutation_conf
            )
            # Insert individual in new population
            individual = self._new_individual(child_genotype)

            new_individuals.append(individual)

        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)

        new_individuals = recovered_individuals + new_individuals

        # create next population
        if self.conf.population_management_selector is not None:
            new_individuals = self.conf.population_management(
                self.individuals,
                new_individuals,
                self.conf.population_management_selector,
            )
        else:
            new_individuals = self.conf.population_management(
                self.individuals, new_individuals
            )
        new_population = Population(
            self.conf, self.simulator_queue, self.analyzer_queue, self.next_robot_id
        )
        new_population.individuals = new_individuals
        logger.info(
            f"Population selected in gen {gen_num} with {len(new_population.individuals)} individuals..."
        )

        return new_population

    async def evaluate(self, new_individuals, gen_num, type_simulation="evolve"):
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        """
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        robot_futures = []
        for individual in new_individuals:
            logger.info(
                f"Evaluating individual (gen {gen_num}) {individual.genotype.id} ..."
            )
            robot_futures.append(
                asyncio.ensure_future(self.evaluate_single_robot(individual))
            )

        await asyncio.sleep(1)

        for i, future in enumerate(robot_futures):
            individual = new_individuals[i]
            logger.info(f"Evaluation of Individual {individual.phenotype.id}")
            (
                individual.fitness,
                individual.phenotype._behavioural_measurements,
            ) = await future

            if individual.phenotype._behavioural_measurements is None:
                assert individual.fitness is None

            if type_simulation == "evolve":
                self.conf.experiment_management.export_behavior_measures(
                    individual.phenotype.id,
                    individual.phenotype._behavioural_measurements,
                )

            logger.info(
                f"Individual {individual.phenotype.id} has a fitness of {individual.fitness}"
            )
            if type_simulation == "evolve":
                self.conf.experiment_management.export_fitness(individual)

    async def evaluate_single_robot(self, individual):
        """
        :param individual: individual
        :return: Returns future of the evaluation, future returns (fitness, [behavioural] measurements)
        """

        if individual.phenotype is None:
            individual.develop()

        # analyze self collisions and robot bounding box
        if self.analyzer_queue is not None:
            collisions, bounding_box = await self.analyzer_queue.test_robot(
                individual, individual.phenotype, self.conf, self._fitness
            )
            if collisions > 0:
                logger.info(
                    f"discarding robot {individual} because there are {collisions} self collisions"
                )
                return None, None
            else:
                individual.phenotype.simulation_boundaries = bounding_box

        # evaluate using directed locomotion according to gongjin's method

        # evaluate this many times in random directions
        number_of_evals = 3

        original_id = individual.phenotype.id

        fitness_list = []
        behaviour_list = []
        target_dir_list = []
        for i in range(number_of_evals):
            # create random target direction vector
            individual.phenotype._id = f"{original_id}_iter_{i+1}"
            target_direction = random.random() * math.pi * 2.0
            target_as_vector: Tuple[float, float, float] = (
                math.cos(target_direction),
                math.sin(target_direction),
                0,
            )
            print(
                f"Target direction of {individual.phenotype._id} = {target_direction}"
            )

            # set target
            assert isinstance(individual.phenotype._brain, BrainCPGTarget)
            individual.phenotype._brain.target = target_as_vector

            # simulate robot and save fitness
            fitness, behaviour = await self.simulator_queue.test_robot(
                individual,
                individual.phenotype,
                self.conf,
                lambda robot_manager, robot: self._fitness(robot_manager, robot),
            )
            fitness_list.append(fitness)
            behaviour_list.append(behaviour)
            target_dir_list.append(target_direction)

        # set robot id back to original id
        individual.phenotype._id = original_id

        fitness_avg = sum(fitness_list) / len(fitness_list)
        behaviour_avg = sum(behaviour_list, start=BehaviouralMeasurements.zero()) / len(
            behaviour_list
        )

        print(f"Fitness values for robot {original_id} = {fitness_list}")
        print(f"Based on targets {target_dir_list}")
        print(f"Average fitness = {fitness_avg}")
        return fitness_avg, behaviour_avg

    @staticmethod
    def _fitness(robot_manager: RobotManager, robot: RevolveBot) -> float:
        """
        Fitness is determined by the formula:

        F = e3 * (e1 / (delta + 1) - penalty_factor * e2)

        Where e1 is the distance travelled in the right direction,
        e2 is the distance of the final position p1 from the ideal
        trajectory starting at starting position p0 and following
        the target direction. e3 is distance in right direction divided by
        length of traveled path(curved) + infinitesimal constant to never divide
        by zero.
        delta is angle between optimal direction and traveled direction.
        """

        penalty_factor = 0.01

        epsilon: float = sys.float_info.epsilon

        # length of traveled path(over the complete curve)
        path_length = measures.path_length(robot_manager)  # L

        # robot position, Vector3(pos.x, pos.y, pos.z)
        pos_0 = robot_manager._positions[0]  # start
        pos_1 = robot_manager._positions[-1]  # end

        # robot displacement
        displacement: Tuple[float, float] = (pos_1[0] - pos_0[0], pos_1[1] - pos_0[1])
        displacement_length = math.sqrt(
            displacement[0] * displacement[0] + displacement[1] * displacement[1]
        )
        displacement_normalized = (
            displacement[0] / displacement_length,
            displacement[1] / displacement_length,
        )

        # steal target from brain
        # is already normalized
        target = robot._brain.target

        # angle between target and actual direction
        delta = math.acos(
            target[0] * displacement_normalized[0]
            + target[1] * displacement_normalized[1]
        )

        # projection of displacement on target line
        dist_in_right_direction: float = (
            displacement[0] * target[0] + displacement[1] * target[1]
        )

        # distance from displacement to target line
        dist_to_optimal_line: float = math.sqrt(
            (dist_in_right_direction * target[0] - displacement[0]) ** 2
            + (dist_in_right_direction * target[1] - displacement[1]) ** 2
        )

        print(
            f"target: {target}, displacement: {displacement}, dist_in_right_direction: {dist_in_right_direction}, dist_to_optimal_line: {dist_to_optimal_line}"
        )

        # filter out passive blocks
        if dist_in_right_direction < 0.01:
            fitness = 0
            print("Did not pass fitness test, fitness = ", fitness)
        else:
            fitness = (dist_in_right_direction / (epsilon + path_length)) * (
                dist_in_right_direction / (delta + 1)
                - penalty_factor * dist_to_optimal_line
            )

            print("Fitness = ", fitness)

        return fitness
