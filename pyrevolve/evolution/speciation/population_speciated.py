from .species import Species
from ..population.population import Population
from ..individual import Individual
from ...custom_logging.logger import logger
from ...evolution.speciation.population_speciated_config import PopulationSpeciatedConfig
from .genus import Genus
from pyrevolve.util.robot_identifier import RobotIdentifier
from pyrevolve.evolution.individual import create_individual


class PopulationSpeciated(Population):
    def __init__(self, config: PopulationSpeciatedConfig, genus: Genus = None):
        # TODO analyzer
        super().__init__(config)
        self.individuals = None # TODO Crash when we should use it

        # Genus contains the collection of different species.
        if genus is None:
            self.genus = Genus(config)
        else:
            self.genus = genus

        self.genomes = []

    async def initialize(self, recovered_individuals=None):
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        individuals = []

        recovered_individuals = [] if recovered_individuals is None else recovered_individuals

        for i in range(self.config.population_size - len(recovered_individuals)):
            individual = create_individual(self.config.genotype_constructor(self.config.genotype_conf))
            individuals.append(individual)

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

        child.genotype.id = RobotIdentifier.getInstance().index()

        # Mutation operator
        child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)

        # Create new individual
        return create_individual(self.config.experiment_management, child_genotype)

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

        # TODO create number of individuals based on the number of recovered individuals.
        new_genus = self.genus.next_generation(recovered_individuals, self._generate_new_individual)

        """
        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)
        """

        # append recovered individuals ## Same as population.next_generation
        # new_individuals = recovered_individuals + new_individuals
        new_population = PopulationSpeciated(self.config, new_genus)
        logger.info(f'Population selected in gen {gen_num} with {len(new_population.individuals)} individuals...')

        return new_population
