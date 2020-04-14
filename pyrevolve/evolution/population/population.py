from __future__ import annotations
import asyncio
import os

from pyrevolve.evolution.individual import Individual
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.population.population_config import PopulationConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Optional
    from pyrevolve.evolution.speciation.species import Species
    from pyrevolve.tol.manage.measures import BehaviouralMeasurements
    from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue, SimulatorQueue


class Population:
    """
    Population class

    It handles the list of individuals: evaluations, mutations and crossovers.
    It is the central component for robot evolution in this framework.
    """

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
        individual.phenotype.update_substrate()
        if parents is not None:
            individual.parents = parents

        self.config.experiment_management.export_genotype(individual)
        self.config.experiment_management.export_phenotype(individual)
        self.config.experiment_management.export_phenotype_images(individual)
        individual.phenotype.measure_phenotype()
        individual.phenotype.export_phenotype_measurements(self.config.experiment_management.data_folder)

        return individual

    def load_snapshot(self, gen_num: int) -> None:
        """
        Recovers all genotypes and fitnesses of robots in the lastest selected population
        :param gen_num: number of the generation snapshot to recover
        """
        data_path = self.config.experiment_management.experiment_folder
        for r, d, f in os.walk(os.path.join(data_path, f'selectedpop_{gen_num}')):
            for file in f:
                if 'body' in file:
                    _id = file.split('.')[0].split('_')[-2]+'_'+file.split('.')[0].split('_')[-1]
                    self.individuals.append(
                        self.config.experiment_management.load_individual(_id, self.config))

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
            individual = self._new_individual(self.config.genotype_constructor(self.config.genotype_conf, self.next_robot_id))
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)
        self.individuals = recovered_individuals + self.individuals

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
            # Selection operator (based on fitness)
            # Crossover
            if self.config.crossover_operator is not None:
                parents = self.config.parent_selection(self.individuals)
                child_genotype = self.config.crossover_operator(parents, self.config.genotype_conf, self.config.crossover_conf)
                child = Individual(child_genotype)
            else:
                child = self.config.selection(self.individuals)

            child.genotype.id = self.next_robot_id
            self.next_robot_id += 1

            # Mutation operator
            child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)
            # Insert individual in new population
            individual = self._new_individual(child_genotype)

            new_individuals.append(individual)

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
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        robot_futures = []
        for individual in new_individuals:
            logger.info(f'Evaluating individual (gen {gen_num}) {individual.id} ...')
            robot_futures.append(asyncio.ensure_future(self.evaluate_single_robot(individual)))

        await asyncio.sleep(1)

        for i, future in enumerate(robot_futures):
            individual = new_individuals[i]
            logger.info(f'Evaluation of Individual {individual.phenotype.id}')
            individual.fitness, individual.phenotype._behavioural_measurements = await future

            if individual.phenotype._behavioural_measurements is None:
                assert (individual.fitness is None)

            if type_simulation == 'evolve':
                self.config.experiment_management.export_behavior_measures(individual.phenotype.id, individual.phenotype._behavioural_measurements)

            logger.info(f'Individual {individual.phenotype.id} has a fitness of {individual.fitness}')
            if type_simulation == 'evolve':
                self.config.experiment_management.export_fitness(individual)

    async def evaluate_single_robot(self, individual: Individual) -> (float, BehaviouralMeasurements):
        """
        :param individual: individual
        :return: Returns future of the evaluation, future returns (fitness, [behavioural] measurements)
        """
        if individual.phenotype is None:
            individual.develop()

        if self.analyzer_queue is not None:
            collisions, bounding_box = await self.analyzer_queue.test_robot(individual, self.config)
            if collisions > 0:
                logger.info(f"discarding robot {individual} because there are {collisions} self collisions")
                return None, None
            else:
                individual.phenotype.simulation_boundaries = bounding_box

        return await self.simulator_queue.test_robot(individual, self.config)
