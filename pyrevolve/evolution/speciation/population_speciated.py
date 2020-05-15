from __future__ import annotations

import os

from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.speciation.species_collection import count_individuals
from pyrevolve.custom_logging.logger import logger
from .genus import Genus
from .species import Species

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional, List, Dict
    from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue, SimulatorQueue
    from pyrevolve.evolution.speciation.population_speciated_config import PopulationSpeciatedConfig


class PopulationSpeciated(Population):
    def __init__(self,
                 config: PopulationSpeciatedConfig,
                 simulator_queue: SimulatorQueue,
                 analyzer_queue: Optional[AnalyzerQueue] = None,
                 next_robot_id: int = 1,
                 next_species_id: int = 1):
        # TODO analyzer
        super().__init__(config, simulator_queue, analyzer_queue, next_robot_id)
        self.config: PopulationSpeciatedConfig = self.config  # this is only for correct type hinting
        self.individuals = None  # TODO Crash when we should use it

        # Genus contains the collection of different species.
        self.genus = Genus(config, next_species_id=next_species_id)

    async def initialize(self, recovered_individuals: Optional[List[Individual]] = None) -> None:
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        assert recovered_individuals is None
        individuals = []

        recovered_individuals = [] if recovered_individuals is None else recovered_individuals

        for i in range(self.config.population_size - len(recovered_individuals)):
            individual = self._new_individual(
                self.config.genotype_constructor(self.config.genotype_conf, self.next_robot_id))
            individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(individuals, 0)
        individuals = recovered_individuals + individuals

        self.genus.speciate(individuals)

    async def next_generation(self,
                              gen_num: int,
                              recovered_individuals: Optional[List[Individual]] = None) -> PopulationSpeciated:
        """
        Creates next generation of the population through selection, mutation, crossover

        :param gen_num: generation number
        :param recovered_individuals: recovered offspring
        :return: new population
        """
        # TODO recovery
        assert recovered_individuals is None
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals

        # TODO create number of individuals based on the number of recovered individuals.
        new_genus = await self.genus.next_generation(
            recovered_individuals,
            self._generate_individual,
            lambda individuals: self.evaluate(individuals, gen_num)
        )

        # append recovered individuals ## Same as population.next_gen
        # new_individuals = recovered_individuals + new_individuals

        new_population = PopulationSpeciated(self.config, self.simulator_queue, self.analyzer_queue, self.next_robot_id)
        new_population.genus = new_genus
        logger.info(f'Population selected in gen {gen_num} '
                    f'with {len(new_population.genus.species_collection)} species '
                    f'and {count_individuals(new_population.genus.species_collection)} individuals.')

        return new_population

    def into_population(self) -> Population:
        new_population = Population(self.config, self.simulator_queue, self.analyzer_queue, self.next_robot_id)
        new_population.individuals = [individual for individual in self.genus.iter_individuals()]
        return new_population

    def _generate_individual(self, individuals: List[Individual]) -> Individual:
        # Selection operator (based on fitness)
        # Crossover
        if self.config.crossover_operator is not None and len(individuals) > 1:
            # TODO The if above may break if the parent_selection needs more than 2 different individuals as input.
            parents = self.config.parent_selection(individuals)
            child_genotype = self.config.crossover_operator(parents, self.config.genotype_conf, self.config.crossover_conf)
            child = Individual(child_genotype)
        else:
            child = self.config.selection(individuals)
            parents = [child]

        child.genotype.id = self.next_robot_id
        self.next_robot_id += 1

        # Mutation operator
        child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)

        # Create new individual
        return self._new_individual(child_genotype, parents)

    def load_snapshot(self, gen_num: int) -> None:
        """
        Recovers all genotypes and fitness of the robots in the `gen_num` generation
        :param gen_num: number of the generation snapshot to recover
        """
        assert gen_num >= 0
        loaded_individuals: Dict[int, Individual] = {}

        def load_individual_fn(_id: int) -> Individual:
            return self.config.experiment_management.load_individual(str(_id), self.config)

        data_path = self.config.experiment_management.generation_folder(gen_num)
        for file in os.scandir(data_path):
            file: os.DirEntry
            if not file.name.startswith('species_'):
                # skip irrelevant files
                continue
            if file.is_file() and file.name.endswith('.yaml'):
                species = Species.Deserialize(file.path, loaded_individuals, load_individual_fn)
                self.genus.species_collection.add_species(species)

        n_loaded_individuals = count_individuals(self.genus.species_collection)
        if n_loaded_individuals != self.config.population_size:
            raise RuntimeError(f'The loaded population ({n_loaded_individuals}) '
                               f'does not match the population size ({self.config.population_size})')
