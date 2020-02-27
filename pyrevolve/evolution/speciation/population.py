from .species import Species
from ..population import Population, PopulationConfig
from ..individual import Individual
from ...custom_logging.logger import logger


class PopulationSpeciatedConfig(PopulationConfig):
    def __init__(self,
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
                 are_genomes_compatible_fn,
                 young_age_threshold: int,
                 young_age_fitness_boost: float,
                 old_age_threshold: int,
                 old_age_fitness_penalty: float,
                 offspring_size=None,
                 next_robot_id=1):
        super().__init__(population_size,
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
                         offspring_size,
                         next_robot_id)
        self.are_genomes_compatible = are_genomes_compatible_fn
        self.young_age_threshold = young_age_threshold
        self.young_age_fitness_boost = young_age_fitness_boost
        self.old_age_threshold = old_age_threshold
        self.old_age_fitness_penalty = old_age_fitness_penalty


class PopulationSpeciated(Population):
    def __init__(self, conf: PopulationSpeciatedConfig, simulator_queue):
        super().__init__(conf, simulator_queue)
        self.genomes = []
        self.species = []
        self._next_species_id = 0

        self._best_species = None

    async def init_pop(self, recovered_individuals=None):
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        await super().init_pop(recovered_individuals)
        self.speciate()

    def speciate(self):
        assert len(self.individuals) > 0

        # clear out the species
        self.species.clear()

        # NOTE: we are comparing the new generation's genomes to the representatives from the previous generation!
        # Any new species that is created is assigned a representative from the new generation.
        for individual in self.individuals:
            genome = individual.genotype
            # Iterate through each species and check if compatible. If compatible, then add the species.
            # If not compatible, create a new species.
            for s in self.species:
                if s.is_compatible(genome, self.conf):
                    s.append(genome)
                    break
            else:
                self.species.append(
                    Species(genome, self._next_species_id)
                )
                self._next_species_id += 1

        self._cleanup_species()

    def generate_new_individual(self, individuals):
        # Selection operator (based on fitness)
        # Crossover
        if self.conf.crossover_operator is not None:
            parents = self.conf.parent_selection(individuals)
            child_genotype = self.conf.crossover_operator(parents, self.conf.genotype_conf, self.conf.crossover_conf)
            child = Individual(child_genotype)
        else:
            child = self.conf.selection(individuals)

        child.genotype.id = self.next_robot_id
        self.next_robot_id += 1

        # Mutation operator
        child_genotype = self.conf.mutation_operator(child.genotype, self.conf.mutation_conf)
        # Insert individual in new population
        return self._new_individual(child_genotype)

    def next_gen(self, gen_num: int, recovered_individuals=None):
        """
        Creates next generation of the population through selection, mutation, crossover

        :param gen_num: generation number
        :param recovered_individuals: recovered offspring
        :return: new population
        """
        # TODO recovery
        assert recovered_individuals is None
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals
        new_individuals = []

        # update species stagnation and stuff
        self.update_species()
        # update adjusted fitnesses
        self.adjust_fitness()
        # calculate offspring amount
        offspring_amounts = self.count_offsprings()

        # Generate new individuals
        for species, offspring_amount in zip(self.species, offspring_amounts):
            for _ in range(offspring_amount):
                species_individuals = [individual for individual, _ in species.iter_individuals()]
                self.generate_new_individual(species_individuals)

        # There are some individuals missing from approximation
        missing_offsprings = self.conf.offspring_size - len(new_individuals)
        assert missing_offsprings >= 0
        best_species = self.species[0]
        for _ in range(missing_offsprings):
            species_individuals = [individual for individual, _ in best_species.iter_individuals()]
            self.generate_new_individual(species_individuals)

        # append recovered individuals
        new_individuals = recovered_individuals + new_individuals

        # create next population
        if self.conf.population_management_selector is not None:
            new_individuals = self.conf.population_management(self.individuals, new_individuals,
                                                              self.conf.population_management_selector)
        else:
            new_individuals = self.conf.population_management(self.individuals, new_individuals)
        new_population = Population(self.conf, self.simulator_queue, self.analyzer_queue, self.next_robot_id)
        new_population.individuals = new_individuals
        logger.info(f'Population selected in gen {gen_num} with {len(new_population.individuals)} individuals...')

        return new_population

    def update_species(self):
        # the old best species will be None at the first iteration
        old_best_species = self._best_species

        # Mark the best species so it is guaranteed to survive.
        self._best_species = max(self.species, key=lambda species: species.get_best_fitness())

        for s in self.species:
            # Reset the species and update its age
            s.increase_age_generations()
            s.increase_gens_no_improvement()
            # TODO remove (how many of this species should be spawned for the next population)
            s.SetOffspringRqd(0)

        # This prevents the previous best species from sudden death
        # If the best species happened to be another one, reset the old
        # species age so it still will have a chance of survival and improvement
        # if it grows old and stagnates again, it is no longer the best one
        # so it will die off anyway.
        if old_best_species is not None:
            old_best_species.reset_age_gens()

    def adjust_fitness(self):
        for s in self.species:
            s.adjust_fitness(s is self._best_species, self.conf)

    def count_offsprings(self):
        assert len(self.individuals) > 0

        total_adjusted_fitness = 0.0

        for i_species in self.species:
            for _, adjusted_fitness in i_species.iter_individuals():
                total_adjusted_fitness += adjusted_fitness

        assert total_adjusted_fitness > 0.0

        average_adjusted_fitness = total_adjusted_fitness / float(len(self.individuals))

        species_offspring_amount = []
        for i_species in self.species:
            offspring_amount = 0.0
            for individual, adjusted_fitness in i_species.iter_individuals():
                offspring_amount += adjusted_fitness / average_adjusted_fitness
            species_offspring_amount.append(round(offspring_amount))

        return species_offspring_amount

    def _cleanup_species(self):
        """
        Remove all empty species (cleanup routine for every case..)
        """
        new_species = []
        for s in self.species:
            if not s.empty():
                new_species.append(s)

        self.species = new_species
