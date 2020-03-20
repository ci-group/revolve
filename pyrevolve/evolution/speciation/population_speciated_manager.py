from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Optional

from pyrevolve.evolution.individual import Individual, create_individual
from pyrevolve.evolution.speciation import PopulationSpeciatedConfig, PopulationSpeciated
from pyrevolve.evolution.speciation.population_speciated import PopulationSpeciated
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.custom_logging.logger import logger
from pyrevolve.tol.manage.measures import BehaviouralMeasurements


class PopulationSpeciatedManager:
    def __init__(self, config: PopulationSpeciatedConfig, simulator_queue: SimulatorQueue, analyzer_queue: AnalyzerQueue):
        self.config = config

        # TODO integrate population and genus dependencies
        self.population = None
        self.genus = None

        self.simulator_queue = simulator_queue
        self.analyzer_queue = analyzer_queue

    async def initialize(self, recovered_individuals: Optional[List[Individual]] = None) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        individuals = []

        recovered_individuals = [] if recovered_individuals is None else recovered_individuals

        for i in range(self.config.population_size - len(recovered_individuals)):
            individuals.append(create_individual(self.config.experiment_management,
                                self.config.genotype_constructor(self.config.genotype_conf)))

        await self.evaluate(individuals, 0)
        individuals = recovered_individuals + individuals

        # TODO difference for speciated
        self.genus.speciate(individuals)

    async def next_generation(self, generation_index: int,
                              recovered_individuals: Optional[List[Individual]] = None) -> PopulationSpeciated:
        """
        Creates next generation of the population through selection, mutation, crossover

        :param generation_index: generation number
        :param recovered_individuals: recovered offspring
        :return: new population
        """
        assert recovered_individuals is None

        recovered_individuals = [] if recovered_individuals is None else recovered_individuals
        new_individuals = self.population.evolve(recovered_individuals)

        # TODO create number of individuals based on the number of recovered individuals.
        new_genus = self.genus.next_generation(recovered_individuals, self._generate_new_individual)

        # evaluate new individuals
        new_individuals = [individual for individual in new_genus.iter_individuals()]
        await self.evaluate(new_individuals, generation_index)

        # append recovered individuals ## Same as population.next_generation
        # new_individuals = recovered_individuals + new_individuals

        new_population = PopulationSpeciated(self.config, new_genus)

        logger.info(f'Population selected in gen {generation_index} '
                    f'with {len(new_population.genus)} species '
                    f'and {new_population.genus.number_of_individuals()} individuals.')

        return new_population

    async def evaluate(self, new_individuals: List[Individual], generation_index: int, type_simulation='evolve') -> None:
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution iteration
        :param generation_index: generation number
        TODO remove `type_simulation`, I have no idea what that is for, but I have a strong feeling it should not be here.
        """
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        robot_futures = []
        for individual in new_individuals:
            logger.info(f'Evaluating individual (gen {generation_index}) {individual.genotype.id} ...')
            robot_futures.append(asyncio.ensure_future(self.evaluate_single_robot(individual)))

        await asyncio.sleep(1)

        for i, future in enumerate(robot_futures):
            individual = new_individuals[i]
            logger.info(f'Evaluation of Individual {individual.phenotype.id}')
            individual.fitness, individual.phenotype._behavioural_measurements = await future

            if individual.phenotype._behavioural_measurements is None:
                assert (individual.fitness is None)

            if type_simulation == 'evolve':
                self.config.experiment_management.export_behavior_measures(individual.phenotype.id,
                                                                           individual.phenotype._behavioural_measurements)

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



