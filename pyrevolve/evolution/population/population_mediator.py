from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, Optional

from pyrevolve.tol.manage.measures import BehaviouralMeasurements
from pyrevolve.evolution.individual import Individual, create_individual
from pyrevolve.evolution.population import PopulationConfig, Population
from pyrevolve.evolution.population.population import create_population
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.logger import logger
from pyrevolve.evolution.population.loader import load_population, load_offspring

from pyrevolve.util.generation import Generation


class PopulationMediator:

    def __init__(self, config: PopulationConfig, simulator_queue: SimulatorQueue, analyzer_queue: AnalyzerQueue):
        self.population = Population(config)

        self.generation = Generation.getInstance()

        self.simulator_queue = simulator_queue
        self.analyzer_queue = analyzer_queue

    async def recover(self, recover_population: bool):
        if recover_population:
            self.population, has_offspring = await load_population(self.population)
            if has_offspring:
                await self.recover_offspring()
        else:
            await self.initialize()

    async def recover_offspring(self):

        individuals = await load_offspring(self.population.config)
        generation_index = self.generation.increment()
        logger.info('Recovered unfinished offspring ' + str(generation_index))

        if generation_index == 0:
            await self.initialize(individuals)
        else:
            self.population = await self.next_generation(individuals)

        self.population.config.experiment_management.export_snapshots(self.population.individuals)

    async def initialize(self, recovered_individuals: Optional[List[Individual]] = None) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        :param recovered_individuals: Individuals that needs to be recovered for the experiment.
        """
        self.population.config.experiment_management.prepare_folders()

        individuals = []
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals

        for i in range(self.population.config.population_size - len(recovered_individuals)):
            individuals.append(create_individual(self.population.config.experiment_management,
                                                 self.population.config.genotype_constructor(self.population.config.genotype_conf)))
        # TODO why evaluate.
        await self.evaluate(individuals)

        individuals = recovered_individuals + individuals
        self.population = Population(self.population.config, individuals)

        self.population.config.experiment_management.export_snapshots(self.population.individuals)

    async def next_generation(self, recovered_individuals: Optional[List[Individual]] = None) -> Population:
        """
        Creates next generation of the population through selection, mutation, crossover

        :param generation_index: generation number
        :param recovered_individuals: recovered offspring
        :return: new population
        """
        assert len(recovered_individuals) == 0

        recovered_individuals = [] if recovered_individuals is None else recovered_individuals
        new_individuals = self.population.evolve(recovered_individuals)

        # evaluate new individuals
        await self.evaluate(new_individuals)

        new_individuals = recovered_individuals + new_individuals
        new_population = create_population(self.population, new_individuals)

        return new_population

    async def evaluate(self, new_individuals: List[Individual], type_simulation='evolve') -> None:
        """
        Evaluates each individual in the new population generation.

        :param new_individuals: newly created population after an evolution iteration
        :param generation_index: generation number
        TODO remove `type_simulation`, I have no idea what that is for, but I have a strong feeling it should not be here.
        """
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        robot_futures = []
        for individual in new_individuals:
            logger.info(f'Evaluating individual (gen {self.generation.index()}) {individual.genotype.id} ...')
            robot_futures.append(asyncio.ensure_future(self._evaluate_robot(individual)))

        await asyncio.sleep(1) # TODO why wait? ...

        for i, future in enumerate(robot_futures):
            individual = new_individuals[i]
            logger.info(f'Evaluation of Individual {individual.phenotype.id}')
            individual.fitness, individual.phenotype._behavioural_measurements = await future

            if individual.phenotype._behavioural_measurements is None:
                assert (individual.fitness is None)

            if type_simulation == 'evolve':
                self.population.config.experiment_management.export_behavior_measures(individual.phenotype.id,
                                                                           individual.phenotype._behavioural_measurements)

            logger.info(f'Individual {individual.phenotype.id} has a fitness of {individual.fitness}')
            if type_simulation == 'evolve':
                self.population.config.experiment_management.export_fitness(individual)

    async def _evaluate_robot(self, individual: Individual) -> (float, BehaviouralMeasurements):
        """
        :param individual: individual
        :return: Returns future of the evaluation, future returns (fitness, [behavioural] measurements)
        """
        if individual.phenotype is None:
            individual.develop()

        if self.analyzer_queue is not None:
            collisions, bounding_box = await self.analyzer_queue.test_robot(individual, self.population.config)
            if collisions > 0:
                logger.info(f"discarding robot {individual} because there are {collisions} self collisions")
                return None, None
            else:
                individual.phenotype.simulation_boundaries = bounding_box

        return await self.simulator_queue.test_robot(individual, self.population.config)


async def create_population_mediator(config: PopulationConfig, simulator_queue: SimulatorQueue,
                                     analyzer_queue: AnalyzerQueue, recover_population: bool):
    population_mediator = PopulationMediator(config, simulator_queue, analyzer_queue)
    await population_mediator.recover(recover_population)