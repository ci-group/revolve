class Species:
    def __init__(self, representative_individuals, species_id: int):
        # list of individuals and adjusted fitnesses
        self._individuals = [(representative_individuals, None)]
        # Individual representative of the species
        self._representative = representative_individuals
        # ID of the species
        self._id = species_id
        # Age of the species (in generations)
        self._age_generations = 0
        # Age of the species (in evaluations)
        self._age_evaluations = 0

        self._generations_with_no_improvements = 0
        self._last_best_fitness = 0  # TODO -Inf

    @property
    def id(self):
        return self._id

    def get_representative(self):
        # return self._individuals[0][0]
        return self._representative

    def is_compatible(self, candidate, population_config):
        return population_config.are_genomes_compatible(candidate, self.get_representative())

    def append(self, genome):
        self._individuals.append((genome, None))

    def empty(self):
        return len(self._individuals) == 0

    def __len__(self):
        return len(self._individuals)

    def iter_individuals(self):
        """
        :return: an iterator of (individual, adjusted_fitness) for all individuals of the species
        """
        return iter(self._individuals)

    # def clear(self):
    #     self._individuals.clear()

    def get_best_fitness(self):
        # TODO cache?
        return max(self._individuals, key=lambda individual: individual[0].fitness)

    def increase_age_evals(self):
        self._age_evaluations += 1

    def increase_age_generations(self):
        self._age_generations += 1

    def increase_gens_no_improvement(self):
        self._generations_with_no_improvements += 1

    def reset_age_gens(self):
        self._age_generations = 0
        self._generations_with_no_improvements = 0

    def adjust_fitness(self, is_best_species: bool, population_config):
        """
        This method performs fitness sharing.
        It also boosts the fitness of the young and penalizes old species

        :param is_best_species: True if this is the best species.
        Fitness adjustment has a different behaviour if the species is the best one.
        :param population_config: collection of configuration parameters
        :type population_config PopulationSpeciatedConfig
        """
        assert not self.empty()

        n_individuals = len(self._individuals)

        for i, (individual, adj_fitness) in enumerate(self._individuals):
            assert individual.fitness is not None
            # TODO can we make this work with negative fitnesses?
            assert individual.fitness >= 0.0

            fitness = individual.fitness

            if fitness == 0.0:
                fitness = 0.0001

            # update the best fitness and stagnation counter
            if fitness >= self._last_best_fitness:
                self._last_best_fitness = fitness
                self._generations_with_no_improvements = 0

            # boost the fitness up to some young age
            if self._age_generations < population_config.young_age_threshold:
                fitness *= population_config.young_age_fitness_boost

            # penalty for old species
            if self._age_generations > population_config.old_age_threshold:
                fitness *= population_config.old_age_fitness_penalty

            # EXTREME penalty if this species is stagnating for too long time
            # one exception if this is the best species found so far
            if not is_best_species \
                    and self._generations_with_no_improvements > population_config.species_max_stagnation:
                fitness *= 0.0000001

            # Compute the adjusted fitness for this member
            self._individuals[i] = (individual, fitness / n_individuals)
