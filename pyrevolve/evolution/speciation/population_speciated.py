from .species import Species
from ..population.population import Population
from ..individual import Individual
from ...custom_logging.logger import logger
from ...evolution.speciation.population_speciated_config import PopulationSpeciatedConfig
from .genus import Genus

class PopulationSpeciated(Population):
    def __init__(self, config: PopulationSpeciatedConfig, simulator_queue, analyzer_queue=None, next_robot_id=1):
        # TODO analyzer
        super().__init__(config, simulator_queue, analyzer_queue, next_robot_id)
        self.individuals = None # TODO Crash when we should use it

        # Genus contains the collection of different species.
        self.genus = Genus(config)

        self.genomes = []

    async def initialize(self, recovered_individuals=None):
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
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

    def _generate_new_individual(self, individuals):
        # Selection operator (based on fitness)
        # Crossover
        if self.config.crossover_operator is not None:
            parents = self.config.parent_selection(individuals)
            child_genotype = self.config.crossover_operator(parents, self.config.genotype_conf, self.config.crossover_conf)
            child = Individual(child_genotype)
        else:
            child = self.config.selection(individuals)

        child.genotype.id = self.next_robot_id
        self.next_robot_id += 1

        # Mutation operator
        child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)

        # Create new individual
        return self._new_individual(child_genotype)

    def next_generation(self, gen_num: int, recovered_individuals=None):
        """
        Creates next generation of the population through selection, mutation, crossover

        :param gen_num: generation number
        :param recovered_individuals: recovered offspring
        :return: new population
        """
        # TODO recovery
        assert recovered_individuals is None
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals

        # TODO do recovery of species
        # TODO remove comments"""
        #             for _i in range(self.conf.offspring_size - len(recovered_individuals)):
        #         # Selection operator (based on fitness)
        #         # Crossover
        #         if self.conf.crossover_operator is not None:
        #             parents = self.conf.parent_selection(self.individuals)
        #             child_genotype = self.conf.crossover_operator(parents, self.conf.genotype_conf, self.conf.crossover_conf)
        #             child = Individual(child_genotype)
        #         else:
        #             child = self.conf.selection(self.individuals)
        #
        #         child.genotype.id = self.next_robot_id
        #         self.next_robot_id += 1
        #
        #         # Mutation operator
        #         child_genotype = self.conf.mutation_operator(child.genotype, self.conf.mutation_conf)
        #         # Insert individual in new population
        #         individual = self._new_individual(child_genotype)
        #
        #         new_individuals.append(individual)
        #         """

        # TODO create number of individuals based on the number of recovered individuals.
        new_genus = self.genus.next_generation(recovered_individuals, self._generate_new_individual)

        """
        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)
        """

        # append recovered individuals ## Same as population.next_gen
        # new_individuals = recovered_individuals + new_individuals

        new_population = PopulationSpeciated(self.config, self.simulator_queue, self.analyzer_queue, self.next_robot_id)
        new_population.genus = new_genus
        logger.info(f'Population selected in gen {gen_num} with {len(new_population.individuals)} individuals...')

        return new_population
