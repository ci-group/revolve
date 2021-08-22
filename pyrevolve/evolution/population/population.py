from __future__ import annotations

import asyncio
import json
import math
import os
import re
from typing import TYPE_CHECKING

import cma
import numpy as np
from pyrevolve.algorithms.revdeknn import RevDEknn
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.revolve_bot.brain.cpg_target import BrainCPGTarget
from pyrevolve.revolve_bot.revolve_bot import RevolveBot
from pyrevolve.tol.manage.measures import BehaviouralMeasurements

if TYPE_CHECKING:
    from typing import Callable, List, Optional, Tuple

    from pyrevolve.tol.manage.robotmanager import RobotManager
    from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue, SimulatorQueue


MULTI_DEV_BODY_PNG_REGEX = re.compile("body_(\\d+)_(\\d+)\\.png")
BODY_PNG_REGEX = re.compile("body_(\\d+)\\.png")


class Population:
    """
    Population class

    It handles the list of individuals: evaluations, mutations and crossovers.
    It is the central component for robot evolution in this framework.
    """

    def __init__(
        self,
        config: PopulationConfig,
        simulator_queue: SimulatorQueue,
        analyzer_queue: Optional[AnalyzerQueue] = None,
        next_robot_id: int = 1,
    ):
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

    def _new_individual(self, genotype, parents: Optional[List[Individual]] = None):
        individual = Individual(genotype)
        individual.develop()
        if isinstance(individual.phenotype, list):
            for alternative in individual.phenotype:
                alternative.update_substrate()
                alternative.measure_phenotype()
                alternative.export_phenotype_measurements(
                    self.config.experiment_management.data_folder
                )
        else:
            individual.phenotype.update_substrate()
            individual.phenotype.measure_phenotype()
            individual.phenotype.export_phenotype_measurements(
                self.config.experiment_management.data_folder
            )
        if parents is not None:
            individual.parents = parents

        self.config.experiment_management.export_genotype(individual)
        self.config.experiment_management.export_phenotype(individual)
        self.config.experiment_management.export_phenotype_images(individual)

        return individual

    def load_snapshot(self, gen_num: int, multi_development=True) -> None:
        """
        Recovers all genotypes and fitnesses of robots in the lastest selected population
        :param gen_num: number of the generation snapshot to recover
        :param multi_development: if multiple developments are created by the same individual
        """
        data_path = self.config.experiment_management.generation_folder(gen_num)
        for r, d, f in os.walk(data_path):
            for filename in f:
                if "body" in filename:
                    if multi_development:
                        _id = MULTI_DEV_BODY_PNG_REGEX.search(filename)
                        if int(_id.group(2)) != 0:
                            continue
                    else:
                        _id = BODY_PNG_REGEX.search(filename)
                    assert _id is not None
                    _id = _id.group(1)
                    self.individuals.append(
                        self.config.experiment_management.load_individual(
                            _id, self.config
                        )
                    )

    def load_offspring(
        self,
        last_snapshot: int,
        population_size: int,
        offspring_size: int,
        next_robot_id: int,
    ) -> List[Individual]:
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

        for robot_id in range(n_robots + 1, next_robot_id):
            # TODO refactor filename
            individuals.append(
                self.config.experiment_management.load_individual(
                    str(robot_id), self.config
                )
            )

        self.next_robot_id = next_robot_id
        return individuals

    async def initialize(
        self, recovered_individuals: Optional[List[Individual]] = None
    ) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        recovered_individuals = (
            [] if recovered_individuals is None else recovered_individuals
        )

        for i in range(self.config.population_size - len(recovered_individuals)):
            new_genotype = self.config.genotype_constructor(
                self.config.genotype_conf, self.next_robot_id
            )
            individual = self._new_individual(new_genotype)
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)
        self.individuals = recovered_individuals + self.individuals

    async def next_generation(
        self, gen_num: int, recovered_individuals: Optional[List[Individual]] = None
    ) -> Population:
        """
        Creates next generation of the population through selection, mutation, crossover

        :param gen_num: generation number
        :param recovered_individuals: recovered offspring
        :return: new population
        """
        recovered_individuals = (
            [] if recovered_individuals is None else recovered_individuals
        )

        new_individuals = []

        for _i in range(self.config.offspring_size - len(recovered_individuals)):
            # Selection operator (based on fitness)
            # Crossover
            parents: Optional[List[Individual]] = None
            if self.config.crossover_operator is not None:
                parents = self.config.parent_selection(self.individuals)
                child_genotype = self.config.crossover_operator(
                    parents, self.config.genotype_conf, self.config.crossover_conf
                )
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
            child_genotype = self.config.mutation_operator(
                child.genotype, self.config.mutation_conf
            )
            # Insert individual in new population
            individual = self._new_individual(child_genotype, parents)

            new_individuals.append(individual)

        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)

        new_individuals = recovered_individuals + new_individuals

        # create next population
        if self.config.population_management_selector is not None:
            new_individuals = self.config.population_management(
                self.individuals,
                new_individuals,
                self.config.population_management_selector,
            )
        else:
            new_individuals = self.config.population_management(
                self.individuals, new_individuals
            )
        new_population = Population(
            self.config, self.simulator_queue, self.analyzer_queue, self.next_robot_id
        )
        new_population.individuals = new_individuals
        logger.info(
            f"Population selected in gen {gen_num} with {len(new_population.individuals)} individuals..."
        )

        return new_population

    async def _evaluate_objectives(
        self, new_individuals: List[Individual], gen_num: int
    ) -> None:
        """
        Evaluates each individual in the new gen population for each objective
        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        """
        assert isinstance(self.config.objective_functions, list) is True
        assert self.config.fitness_function is None

        robot_futures = []
        for individual in new_individuals:
            individual.develop()
            individual.objectives = [
                -math.inf for _ in range(len(self.config.objective_functions))
            ]

            assert len(individual.phenotype) == len(self.config.objective_functions)
            for objective, robot in enumerate(individual.phenotype):
                logger.info(
                    f"Evaluating individual (gen {gen_num} - objective {objective}) {robot.id}"
                )
                objective_fun = self.config.objective_functions[objective]
                future = asyncio.ensure_future(
                    self.evaluate_single_robot(
                        individual=individual,
                        fitness_fun=objective_fun,
                        phenotype=robot,
                    )
                )
                robot_futures.append((individual, robot, objective, future))

        await asyncio.sleep(1)

        for individual, robot, objective, future in robot_futures:
            assert objective < len(self.config.objective_functions)

            logger.info(f"Evaluation of Individual (objective {objective}) {robot.id}")
            fitness, robot._behavioural_measurements = await future
            individual.objectives[objective] = fitness
            logger.info(
                f"Individual {individual.id} in objective {objective} has a fitness of {fitness}"
            )

            if robot._behavioural_measurements is None:
                assert fitness is None

            self.config.experiment_management.export_behavior_measures(
                robot.id, robot._behavioural_measurements, objective
            )

        for individual, robot, objective, _ in robot_futures:
            self.config.experiment_management.export_objectives(individual)

    async def evaluate(
        self, new_individuals: List[Individual], gen_num: int, type_simulation="evolve"
    ) -> None:
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        TODO remove `type_simulation`, I have no idea what that is for, but I have a strong feeling it should not be here.
        """
        if callable(self.config.fitness_function):
            await self._evaluate_single_fitness(
                new_individuals, gen_num, type_simulation
            )
        elif isinstance(self.config.objective_functions, list):
            await self._evaluate_objectives(new_individuals, gen_num)
        else:
            raise RuntimeError("Fitness function not configured correctly")

    async def _evaluate_single_fitness(
        self, new_individuals: List[Individual], gen_num: int, type_simulation="evolve"
    ) -> None:
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        robot_futures = []
        for individual in new_individuals:
            logger.info(f"Evaluating individual (gen {gen_num}) {individual.id} ...")
            assert callable(self.config.fitness_function)
            robot_futures.append(
                asyncio.ensure_future(
                    self.evaluate_single_robot(
                        individual=individual, fitness_fun=self.config.fitness_function
                    )
                )
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
                self.config.experiment_management.export_behavior_measures(
                    individual.phenotype.id,
                    individual.phenotype._behavioural_measurements,
                    None,
                )

            logger.info(
                f"Individual {individual.phenotype.id} has a fitness of {individual.fitness}"
            )
            if type_simulation == "evolve":
                self.config.experiment_management.export_fitness(individual)

    # gets fitness of an individual but can apply a learning algorithm first
    async def evaluate_single_robot(
        self,
        individual: Individual,
        fitness_fun: Callable[[RobotManager, RevolveBot], float],
        phenotype: Optional[RevolveBot] = None,
    ) -> Tuple[float, BehaviouralMeasurements]:
        if self.config.learner == "disabled":
            return await self.get_fitness(individual, fitness_fun, phenotype)
        elif self.config.learner == "revdeknn":
            return await self.get_fitness_revdeknn(individual, fitness_fun, phenotype)
        elif self.config.learner == "cmaes":
            return await self.get_fitness_cmaes(individual, fitness_fun, phenotype)
        else:
            raise NotImplementedError(
                f"learner type not supported: {self.config.learner}"
            )

    # get fitness of individual, but apply learner algorithm revdeknn first
    async def get_fitness_revdeknn(
        self,
        individual: Individual,
        fitness_fun: Callable[[RobotManager, RevolveBot], float],
        phenotype: Optional[RevolveBot] = None,
    ) -> Tuple[float, BehaviouralMeasurements]:
        # TODO does revdeknn like high or low fitness values?
        # what is the best fitness value? how do we get it from the alg

        if phenotype is None:
            if individual.phenotype is None:
                individual.develop()
            phenotype = individual.phenotype

        initial_pop_count = 3
        gauss_sigma = 1.0
        iterations = 1

        revde_gamma = 0.5
        revde_cr = 0.9

        if len(phenotype.brain.weights) == 0:
            return await self.get_fitness(individual, fitness_fun, phenotype)

        initial_weights = phenotype.brain.weights

        # create array of 99 arrays
        # each array is for an individual
        # all entries are weight modifiers from  anormal distribition
        # so each array is same length as number of weights
        population = np.random.normal(
            0, gauss_sigma, (initial_pop_count - 1, len(initial_weights))
        )
        # add entry for original brain with 0 modifiers
        population = np.append([[0] * len(initial_weights)], population, 0)

        # add brain weights to each of the modifiers so we get `initial_pop_count` different brains
        # altered by a gaussian distribution
        population = np.array(
            list(map(lambda mods: np.add(mods, initial_weights), population))
        )

        # index used by `_get_fitness_revdeknn_evaluate_weights` to make unique robot ids
        phenotype.revdeknn_i = 0

        fitnesses = [
            await self._get_fitness_revdeknn_evaluate_weights(
                individual, fitness_fun, phenotype, weights
            )
            for weights in population
        ]

        es = RevDEknn(
            lambda theta: (
                await self._get_fitness_revdeknn_evaluate_weights_all(
                    individual, fitness_fun, phenotype, theta
                )
                for _ in "_"
            ).__anext__(),  # extremely ugly hack to get await in a lambda as I don't have time to make a good interface for revdeknn
            revde_gamma,
            -1.0,
            1.0,
            revde_cr,
        )

        for _ in range(iterations):
            population, fitnesses = await es.step(population, fitnesses)

        delattr(phenotype, "revdeknn_i")

        print("AAAAAAAAAAAAA")
        print(fitnesses)

        # best fitness could also be retrieved from last element in the fitnesses array
        # but we want an entry in the output logs for the best one
        # and the easiest way to get that is to just evaluate again
        original_weights = phenotype.brain.weights
        phenotype.brain.weights = population[0]
        fitness, behaviour = await self.get_fitness(individual, fitness_fun, phenotype)
        phenotype.brain.weights = original_weights

        return fitness, behaviour

    async def _get_fitness_revdeknn_evaluate_weights_all(
        self,
        individual: Individual,
        fitness_fun: Callable[[RobotManager, RevolveBot], float],
        phenotype: RevolveBot,
        theta: np.ndarray,  # mxn matrix
    ):
        return [
            await self._get_fitness_revdeknn_evaluate_weights(
                individual, fitness_fun, phenotype, weights
            )
            for weights in theta
        ]

    async def _get_fitness_revdeknn_evaluate_weights(
        self,
        individual: Individual,
        fitness_fun: Callable[[RobotManager, RevolveBot], float],
        phenotype: RevolveBot,
        weights: List[float],
    ) -> float:
        original_weights = phenotype.brain.weights
        phenotype.brain.weights = weights
        original_id = phenotype.id
        phenotype._id = f"{original_id}_revdeknn_{phenotype.revdeknn_i}"
        fitness, _ = await self.get_fitness(individual, fitness_fun, phenotype)
        phenotype.brain.weights = original_weights
        phenotype._id = original_id
        phenotype.revdeknn_i += 1
        return [fitness]

    # get fitness of individual, but apply learner algorithm cmaes first
    async def get_fitness_cmaes(
        self,
        individual: Individual,
        fitness_fun: Callable[[RobotManager, RevolveBot], float],
        phenotype: Optional[RevolveBot] = None,
    ) -> Tuple[float, BehaviouralMeasurements]:
        if phenotype is None:
            if individual.phenotype is None:
                individual.develop()
            phenotype = individual.phenotype

        if len(phenotype.brain.weights) <= 1:
            if len(phenotype.brain.weights) == 1:
                logger.warn(
                    "Brain with one weight not optimized. CMAES library does not support 1D."
                )
            return await self.get_fitness(individual, fitness_fun, phenotype)

        es = cma.CMAEvolutionStrategy(
            phenotype.brain.weights,
            0.5,
            {"maxfevals": "100", "maxiter": "100/(4 + 3 * np.log(N))"},
        )
        phenotype.cmaes_i = 0
        while not es.stop():
            solutions = es.ask()
            es.tell(
                solutions,
                [
                    await self._get_fitness_cmaes_evaluate_weights(
                        individual, fitness_fun, phenotype, weights
                    )
                    for weights in solutions
                ],
            )

        delattr(phenotype, "cmaes_i")

        # best fitness could also be retrieved from es.result.xbest
        # but we want an entry in the output logs for the best one
        # and the easiest way to get that is to just evaluate again
        original_weights = phenotype.brain.weights
        phenotype.brain.weights = es.result.xbest
        fitness, behaviour = await self.get_fitness(individual, fitness_fun, phenotype)
        phenotype.brain.weights = original_weights

        return fitness, behaviour

    async def _get_fitness_cmaes_evaluate_weights(
        self,
        individual: Individual,
        fitness_fun: Callable[[RobotManager, RevolveBot], float],
        phenotype: RevolveBot,
        weights: List[float],
    ) -> float:
        original_weights = phenotype.brain.weights
        phenotype.brain.weights = weights
        original_id = phenotype.id
        phenotype._id = f"{original_id}_cmaes_{phenotype.cmaes_i}"
        fitness, _ = await self.get_fitness(individual, fitness_fun, phenotype)
        phenotype.brain.weights = original_weights
        phenotype._id = original_id
        phenotype.cmaes_i += 1
        return fitness

    # call this to get the fitness of a single robot instance.
    async def get_fitness(
        self,
        individual: Individual,
        fitness_fun: Callable[[RobotManager, RevolveBot], float],
        phenotype: Optional[RevolveBot] = None,
    ) -> Tuple[float, BehaviouralMeasurements]:
        """
        :param individual: individual
        :param fitness_fun: fitness function
        :param phenotype: robot phenotype to test [optional]
        :return: Returns future of the evaluation, future returns (fitness, [behavioural] measurements)
        """
        # evaluate this many times in random directions
        number_of_evals = 3

        if phenotype is None:
            if individual.phenotype is None:
                individual.develop()
            phenotype = individual.phenotype

        assert isinstance(phenotype, RevolveBot)

        if self.analyzer_queue is not None:
            collisions, bounding_box = await self.analyzer_queue.test_robot(
                individual, phenotype, self.config, fitness_fun
            )
            if collisions > 0:
                logger.info(
                    f"discarding robot {individual} because there are {collisions} self collisions"
                )
                return None, None
            else:
                phenotype.simulation_boundaries = bounding_box

        # evaluate using directed locomotion according to gongjin's method
        original_id = phenotype.id

        fitness_list = []
        behaviour_list = []
        target_dir_list = []
        for i in range(number_of_evals):
            # create random target direction vector
            phenotype._id = f"{original_id}_iter_{i+1}"
            target_direction = math.pi * 2.0 / number_of_evals * i
            target: Tuple[float, float, float] = (
                math.cos(target_direction) * self.config.target_distance,
                math.sin(target_direction) * self.config.target_distance,
                0,
            )
            logger.info(f"Target direction of {phenotype._id} = {target_direction}")

            # set target
            assert isinstance(phenotype._brain, BrainCPGTarget)
            phenotype._brain.target = target

            # simulate robot and save fitness
            fitness, behaviour = await self.simulator_queue.test_robot(
                individual,
                individual.phenotype,
                self.config,
                lambda robot_manager, robot: self._fitness_robotmanager_hook(
                    fitness_fun,
                    self.config.experiment_management.experiment_folder,
                    robot_manager,
                    robot,
                ),
            )
            fitness_list.append(fitness)
            behaviour_list.append(behaviour)
            target_dir_list.append(target_direction)

            with open(
                f"{self.config.experiment_management.experiment_folder}/data_fullevolution/fitness/fitness_robot_{phenotype._id}.txt",
                "w",
            ) as file:
                file.write(str(fitness))

        # set robot id back to original id
        phenotype._id = original_id

        fitness_avg = sum(fitness_list) / len(fitness_list)
        behaviour_avg = sum(behaviour_list, start=BehaviouralMeasurements.zero()) / len(
            behaviour_list
        )

        with open(
            f"{self.config.experiment_management._fitness_folder}/fitness_robot_{phenotype._id}.txt",
            "w",
        ) as file:
            file.write(str(fitness_avg))

        print(f"Fitness values for robot {original_id} = {fitness_list}")
        print(f"Based on targets {target_dir_list}")
        print(f"Average fitness = {fitness_avg}")
        return fitness_avg, behaviour_avg

    # acts as a proxy for the fitness function, but man in the middles to use the robot manager
    # to store the complete simulation history
    # very ugly but lets just make it work for this experiment
    @staticmethod
    def _fitness_robotmanager_hook(
        fitness_function,
        path: str,
        robot_manager: RobotManager,
        robot: RevolveBot,
    ) -> float:
        # secretly save the simulation history
        Population._save_simulation_history(robot_manager, path, robot.id)

        # do actual fitness calculation
        return fitness_function(robot_manager, robot)

    @staticmethod
    def _save_simulation_history(robot_manager: RobotManager, path: str, robot_id: str):
        with open(
            path + "/data_fullevolution/descriptors/simulation_" + robot_id + ".json",
            "w",
        ) as file:
            output = []
            for i in range(len(robot_manager._positions)):
                orientation_vecs = {}
                for key in robot_manager._orientation_vecs[i].keys():
                    item = robot_manager._orientation_vecs[i][key]
                    orientation_vecs[key.name.lower()] = (item[0], item[1], item[2])
                output.append(
                    {
                        "info": "'orientation' is euler angles.",
                        "position": (
                            robot_manager._positions[i][0],
                            robot_manager._positions[i][2],
                            robot_manager._positions[i][2],
                        ),
                        "orientation": (
                            robot_manager._orientations[i][0],
                            robot_manager._orientations[i][1],
                            robot_manager._orientations[i][2],
                        ),
                        "time": str(robot_manager._times[i]),
                        # pretty sure you can derive the following from the above
                        #  but saving them just to be sure
                        "ds": robot_manager._ds[i],
                        "dt": robot_manager._dt[i],
                        "orientation_vecs": orientation_vecs,
                        "seconds": robot_manager._seconds[i],
                    }
                )
            file.write(json.dumps(output))
