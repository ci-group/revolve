from __future__ import annotations

import math
import os
import re

import asyncio

from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution import fitness
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.revolve_bot.revolve_bot import RevolveBot
from pyrevolve.tol.manage.measures import BehaviouralMeasurements

from typing import TYPE_CHECKING, AnyStr

if TYPE_CHECKING:
    from typing import List, Optional, Callable, Tuple
    from pyrevolve.tol.manage.robotmanager import RobotManager

    from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue, SimulatorQueue


MULTI_DEV_BODY_PNG_REGEX = re.compile('body_(\\d+)_(\\d+)\\.png')
BODY_PNG_REGEX = re.compile('body_(\\d+)\\.png')


class Population:
    """
    Population class

    It handles the list of individuals: evaluations, mutations and crossovers.
    It is the central component for robot evolution in this framework.
    """

    config: PopulationConfig
    individual: List[Individual]
    analyzer_queue: Optional[AnalyzerQueue]
    SimulatorQueue: SimulatorQueue
    next_robot_id: int

    def __init__(self,
                 config: PopulationConfig,
                 simulator_queue: SimulatorQueue,
                 analyzer_queue: Optional[AnalyzerQueue] = None,
                 next_robot_id: int = 1):
        """
        Creates a Population object that initialises the
        individuals in the population with an empty list
        and stores the configuration of the system to the
        conf variable.

        :param config: configuration of the system
        :param simulator_queue: connection to the simulator queue
        :param analyzer_queue: connection to the analyzer simulator queue
        :param next_robot_id: (sequential) id of the next individual to be created
        """
        self.config = config
        self.individuals = []
        self.analyzer_queue = analyzer_queue
        self.simulator_queue = simulator_queue
        self.next_robot_id = next_robot_id

    def _new_individual(self,
                        genotype,
                        parents: Optional[List[Individual]] = None):
        individual = Individual(genotype)
        individual.develop()
        if isinstance(individual.phenotype, list):
            for alternative in individual.phenotype:
                alternative.update_substrate()
                alternative.measure_phenotype()
                alternative.export_phenotype_measurements(self.config.experiment_management.data_folder)
        else:
            individual.phenotype.update_substrate()
            individual.phenotype.measure_phenotype()
            individual.phenotype.export_phenotype_measurements(self.config.experiment_management.data_folder)
        if parents is not None:
            individual.parents = parents

        self.config.experiment_management.export_genotype(individual)
        self.config.experiment_management.export_phenotype(individual)
        self.config.experiment_management.export_phenotype_images(individual)

        return individual

    def load_snapshot(self, gen_num: int, multi_development=False) -> None:
        """
        Recovers all genotypes and fitnesses of robots in the lastest selected population
        :param gen_num: number of the generation snapshot to recover
        :param multi_development: if multiple developments are created by the same individual
        """
        data_path = self.config.experiment_management.generation_folder(gen_num)
        for r, d, f in os.walk(data_path):
            for filename in f:
                if 'body' in filename:
                    if multi_development:
                        _id = MULTI_DEV_BODY_PNG_REGEX.search(filename)
                        if int(_id.group(2)) != 0:
                            continue
                    else:
                        _id = BODY_PNG_REGEX.search(filename)
                    assert _id is not None
                    _id = _id.group(1)
                    self.individuals.append(
                        self.config.experiment_management.load_individual(_id, self.config))

    def load_external_snapshot(self, run_folder: AnyStr, gen_num: int, multi_development=True) -> int:
        """
        Reads and loads all genotypes of robots in the population found in the data folder.
        Fitness values are zero by default.

        :param run_folder: folder where to load the data from (run folder)
        :param gen_num: generation number
        :param multi_development: if multiple developments are created by the same individual
        :return: number of individuals loaded
        """
        generation_folder_path = os.path.join(run_folder, ExperimentManagement.GENERATIONS_FOLDER, f"generation_{gen_num}")
        data_folder_path = os.path.join(run_folder, ExperimentManagement.DATA_FOLDER)
        counter = 0
        for r, d, f in os.walk(generation_folder_path):
            for filename in f:
                if 'body' in filename:
                    if multi_development:
                        _id = MULTI_DEV_BODY_PNG_REGEX.search(filename)
                        if int(_id.group(2)) != 0:
                            continue
                    else:
                        _id = BODY_PNG_REGEX.search(filename)
                    assert _id is not None
                    _id = _id.group(1)
                    genotype_file = os.path.join(data_folder_path, 'genotypes', f'genotype_{_id}.txt')
                    individual = self.config.experiment_management.load_external_individual(genotype_file, _id,
                                                                                            self.config)
                    self.individuals.append(individual)
                    self.next_robot_id = max(self.next_robot_id, int(_id))
                    counter += 1
        self.next_robot_id += 1
        return counter

    def load_offspring(self,
                       last_snapshot: int,
                       population_size: int,
                       offspring_size: int,
                       next_robot_id: int) -> List[Individual]:
        """
        Recovers the part of an unfinished offspring
        :param last_snapshot: number of robots expected until the latest snapshot
        :param population_size: Population size
        :param offspring_size: Offspring size (steady state)
        :param next_robot_id: TODO
        :return: the list of recovered individuals
        """
        individuals = []
        # number of robots expected until the latest snapshot
        if last_snapshot == -1:
            n_robots = 0
        else:
            n_robots = population_size + last_snapshot * offspring_size

        for robot_id in range(n_robots+1, next_robot_id):
            #TODO refactor filename
            individuals.append(
                self.config.experiment_management.load_individual(str(robot_id), self.config)
            )

        self.next_robot_id = next_robot_id
        return individuals

    async def initialize(self, recovered_individuals: Optional[List[Individual]] = None) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals

        for i in range(self.config.population_size-len(recovered_individuals)):
            new_genotype = self.config.genotype_constructor(self.config.genotype_conf, self.next_robot_id)
            individual = self._new_individual(new_genotype)
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)
        self.individuals = recovered_individuals + self.individuals

    async def initialize_from_single_individual(self, progenitor: Optional[Individual] = None) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        All individuals are based on a single random individual (one progenitor for all solutions)
        """
        progenitor_genotype = None
        for i in range(self.config.population_size):
            if progenitor_genotype is None:
                # first loop iteration
                if progenitor is None:
                    # generate random progenitor
                    progenitor_genotype = self.config.genotype_constructor(self.config.genotype_conf, self.next_robot_id)
                    progenitor = self._new_individual(progenitor_genotype)
                else:
                    # use the one provided as parameter
                    progenitor_genotype = progenitor.genotype
                individual = progenitor
            else:
                # all remaining loop iterations
                new_genotype = self.config.mutation_operator(progenitor_genotype, self.config.mutation_conf)
                new_genotype.id = self.next_robot_id
                individual = self._new_individual(new_genotype, [progenitor])
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)

    async def next_generation(self,
                              gen_num: int,
                              recovered_individuals: Optional[List[Individual]] = None) -> Population:
        """
        Creates next generation of the population through selection, mutation, crossover

        :param gen_num: generation number
        :param recovered_individuals: recovered offspring
        :return: new population
        """
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals

        new_individuals = []

        for _i in range(self.config.offspring_size-len(recovered_individuals)):
            for i in range(1000):
                # Selection operator (based on fitness)
                # Crossover
                parents: Optional[List[Individual]] = None
                if self.config.crossover_operator is not None:
                    parents = self.config.parent_selection(self.individuals)
                    child_genotype = self.config.crossover_operator(parents, self.config.genotype_conf, self.config.crossover_conf)
                    # temporary individual that will be used for mutation
                    child = Individual(child_genotype)
                    child.parents = parents
                else:
                    # fake child
                    child = self.config.selection(self.individuals)
                    parents = [child]

                child.genotype.id = self.next_robot_id
                self.next_robot_id += 1

                # Mutation operator
                child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)

                if self.config.genotype_test(child_genotype):
                    # valid individual found, exit infinite loop
                    # Insert individual in new population
                    individual = self._new_individual(child_genotype, parents)
                    new_individuals.append(individual)
                    break
            else:
                # genotype test not passed
                raise RuntimeError("New individual not found, crashing now :)")

        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)

        new_individuals = recovered_individuals + new_individuals

        # create next population
        if self.config.population_management_selector is not None:
            new_individuals = self.config.population_management(self.individuals,
                                                                new_individuals,
                                                                self.config.population_management_selector)
        else:
            new_individuals = self.config.population_management(self.individuals, new_individuals)
        new_population = Population(self.config,
                                    self.simulator_queue,
                                    self.analyzer_queue,
                                    self.next_robot_id)
        new_population.individuals = new_individuals
        logger.info(f'Population selected in gen {gen_num} with {len(new_population.individuals)} individuals...')

        return new_population

    async def _evaluate_objectives(self,
                                  new_individuals: List[Individual],
                                  gen_num: int) -> None:
        """
        Evaluates each individual in the new gen population for each objective
        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        """
        assert isinstance(self.config.objective_functions, list) is True
        assert self.config.fitness_function is None

        if hasattr(self.simulator_queue, 'test_robot'):
            robot_futures = []
            for individual in new_individuals:
                individual.develop()
                individual.objectives = [-math.inf for _ in range(len(self.config.objective_functions))]

                assert len(individual.phenotype) == len(self.config.objective_functions)
                for objective, robot in enumerate(individual.phenotype):
                    logger.info(f'Evaluating individual (gen {gen_num} - objective {objective}) {robot.id}')
                    objective_fun = self.config.objective_functions[objective]
                    future = asyncio.ensure_future(
                        self.evaluate_single_robot(individual=individual, fitness_fun=objective_fun, phenotype=robot))
                    robot_futures.append((individual, robot, objective, future))

            await asyncio.sleep(1)
        elif hasattr(self.simulator_queue, 'test_population'):
            raise NotImplementedError(
                "Test an entire population at once is not implemented when using multiple objectives")
        else:
            raise AttributeError("Simulator queue object does not implement either 'test_robot' or 'test_population'")

        for individual, robot, objective, future in robot_futures:
            assert objective < len(self.config.objective_functions)

            logger.info(f'Evaluation of Individual (objective {objective}) {robot.id}')
            fitness, robot._behavioural_measurements = await future
            individual.objectives[objective] = fitness
            logger.info(f'Individual {individual.id} in objective {objective} has a fitness of {fitness}')

            if robot._behavioural_measurements is None:
                assert fitness is None

            self.config.experiment_management\
                .export_behavior_measures(robot.id, robot._behavioural_measurements, objective)

        for individual, robot, objective, _ in robot_futures:
            self.config.experiment_management.export_objectives(individual)

    async def evaluate(self,
                       new_individuals: List[Individual],
                       gen_num: int,
                       type_simulation = 'evolve') -> None:
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        TODO remove `type_simulation`, I have no idea what that is for, but I have a strong feeling it should not be here.
        """
        if callable(self.config.fitness_function):
            await self._evaluate_single_fitness(new_individuals, gen_num, type_simulation)
        elif isinstance(self.config.objective_functions, list):
            await self._evaluate_objectives(new_individuals, gen_num)
        else:
            raise RuntimeError("Fitness function not configured correctly")

    async def _evaluate_single_fitness(self,
                                       new_individuals: List[Individual],
                                       gen_num: int,
                                       type_simulation = 'evolve') -> None:
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        assert callable(self.config.fitness_function)

        robot_fitnesses: List[float] = []
        robot_behaviours: List[BehaviouralMeasurements] = []
        if hasattr(self.simulator_queue, 'test_robot'):
            robot_futures = []
            for individual in new_individuals:
                logger.info(f'Evaluating individual (gen {gen_num}) {individual.id} ...')
                robot_futures.append(
                    asyncio.ensure_future(
                        self.evaluate_single_robot(individual=individual, fitness_fun=self.config.fitness_function)))
            await asyncio.sleep(1)
            for future in robot_futures:
                fitness, behaviour = await future
                robot_fitnesses.append(fitness)
                robot_behaviours.append(behaviour)

        elif hasattr(self.simulator_queue, 'test_population'):
            logger.info(f'Evaluating whole population (gen {gen_num}) ...')
            robot_fitnesses, robot_behaviours = await self.evaluate_whole_population(population=new_individuals, fitness_fun=self.config.fitness_function)

        else:
            raise AttributeError("Simulator queue object does not implement either 'test_robot' or 'test_population'")

        for individual, fitness, behaviour in zip(new_individuals, robot_fitnesses, robot_behaviours):
            logger.info(f'Evaluation of Individual {individual.phenotype.id}')
            individual.fitness = fitness
            individual.phenotype._behavioural_measurements = behaviour

            if individual.phenotype._behavioural_measurements is None:
                assert (individual.fitness is None)

            if type_simulation == 'evolve':
                self.config.experiment_management.export_behavior_measures(individual.phenotype.id,
                                                                           individual.phenotype._behavioural_measurements,
                                                                           None)

            logger.info(f'Individual {individual.phenotype.id} has a fitness of {individual.fitness}')
            if type_simulation == 'evolve':
                self.config.experiment_management.export_fitness(individual)

    async def evaluate_single_robot(self,
                                    individual: Individual,
                                    fitness_fun: Callable[[RobotManager, RevolveBot], float],
                                    phenotype: Optional[RevolveBot] = None) -> Tuple[float, BehaviouralMeasurements]:
        """
        :param individual: individual
        :param fitness_fun: fitness function
        :param phenotype: robot phenotype to test [optional]
        :return: Returns future of the evaluation, future returns (fitness, [behavioural] measurements)
        """
        if phenotype is None:
            if individual.phenotype is None:
                individual.develop()
            phenotype = individual.phenotype

        assert isinstance(phenotype, RevolveBot)

        if self.analyzer_queue is not None:
            collisions, bounding_box = await self.analyzer_queue.test_robot(individual, phenotype, self.config, fitness_fun)
            if collisions > 0:
                logger.info(f"discarding robot {individual} because there are {collisions} self collisions")
                return None, None
            else:
                phenotype.simulation_boundaries = bounding_box

        if self.simulator_queue is not None:
            return await self.simulator_queue.test_robot(individual, phenotype, self.config, fitness_fun)
        else:
            print("MOCKING SIMULATION")
            return await self._mock_simulation()

    async def evaluate_whole_population(self,
                                        population: List[Individual],
                                        fitness_fun: Callable[[RobotManager, RevolveBot], float]) \
            -> Tuple[List[Optional[float]], List[Optional[BehaviouralMeasurements]]]:
        phenotypes = []
        for individual in population:
            if individual.phenotype is None:
                individual.develop()
            phenotypes.append(individual.phenotype)

        skip: List[int] = []
        if self.analyzer_queue is not None:
            for i, phenotype in enumerate(phenotypes):
                collisions, bounding_box = await self.analyzer_queue.test_robot(individual, phenotype, self.config, fitness_fun)
                if collisions > 0:
                    logger.info(f"discarding robot {individual} because there are {collisions} self collisions")
                    skip.append(i)
                else:
                    phenotype.simulation_boundaries = bounding_box

        for i in skip:
            del population[i]
            del phenotypes[i]

        fitnesses = []
        behaviours = []
        from pyrevolve.util.iterables import iter_group
        for i, phenotype_batch in enumerate(iter_group(phenotypes, self.config.population_batch_size)):
            phenotype_batch = [ind for ind in phenotype_batch]
            logger.info(f'Evaluating batch ({i}): {phenotype_batch}')
            if len(phenotype_batch) == 0:
                break
            assert len(phenotype_batch) == self.config.population_batch_size
            fitnesses_, behaviours_ = await self.simulator_queue.test_population(population, phenotype_batch, self.config, fitness_fun)
            fitnesses += fitnesses_
            behaviours += behaviours_

        assert len(fitnesses) == len(phenotypes)

        # TODO verify that these are correctly positioned
        for i in skip:
            fitnesses.insert(i, None)
            behaviours.insert(i, None)

        return fitnesses, behaviours

    @staticmethod
    async def _mock_simulation():
        return fitness.random(None, None), BehaviouralMeasurements()
