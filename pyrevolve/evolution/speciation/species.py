from __future__ import annotations
import math
from pyrevolve.evolution.speciation.age import Age

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Optional
    from pyrevolve.evolution.individual import Individual
    from .population_speciated_config import PopulationSpeciatedConfig
    from pyrevolve.genotype.genotype import Genotype



class Species:
    """
    Collection of individuals that share the same Species
    I.e. they have compatible genomes and are considered similar individuals/solutions.
    A crossover between two individuals of the same species is supposed to have a good fitness.
    """

    def __init__(self, individuals: List[Individual], species_id: int, age: Age = None, best_fitness: float = 0.0):

        # list of individuals and adjusted fitnesses
        # TODO _adjusted_fitness name to split off from regular individuals
        self._individuals: List[(Individual, Optional[float])] = [(individual, None) for individual in individuals]
        # Individual representative of the species
        self._representative: Individual = individuals[0]  # TODO is this always the first individual?

        # ID of the species
        self._id: int = species_id

        self.age: Age = Age() if age is None else age

        # Fitness
        self._last_best_fitness: float = best_fitness  # TODO -Inf |-float('Inf')|

    # TODO refactor population_config
    def is_compatible(self, candidate: Individual, population_config: PopulationSpeciatedConfig) -> bool:
        """
        Tests if the candidate individual is compatible with this Species
        :param candidate: candidate individual to test against the current species
        :param population_config: config where to pick the `are genomes compatible` function
        :return: if the candidate individual is compatible or not
        """
        return population_config.are_genomes_compatible(candidate.genotype, self._representative.genotype)

    # TODO duplicate code with species collection best/worst function
    def get_best_fitness(self) -> float:
        """
        Finds the best fitness for individuals in the species. If the species is empty, it returns negative infinity.
        :return: the best fitness in the species.
        """
        if self.empty():
            return -math.inf
        return self.get_best_individual().fitness

    def get_best_individual(self) -> Individual:
        """
        :return: the best individual of the species
        """
        # TODO cache?
        # all the individuals should have fitness defined
        return max(self._individuals, key=lambda individual: individual[0].fitness)

    # TODO refactor population_config
    def adjust_fitness(self, is_best_species: bool, population_config: PopulationSpeciatedConfig) -> None:
        """
        This method performs fitness sharing. It computes the adjusted fitness of the individuals.
        It also boosts the fitness of the young and penalizes old species

        :param is_best_species: True if this is the best species.
        Fitness adjustment has a different behaviour if the species is the best one.
        :param population_config: collection of configuration parameters
        :type population_config PopulationSpeciatedConfig
        """
        assert not self.empty()

        n_individuals = len(self._individuals)

        for individual_index, (individual, _) in enumerate(self._individuals):
            assert individual.fitness is not None
            assert individual.fitness >= 0.0  # TODO can we make this work with negative fitnesses?

            fitness = self._modify_fitness(individual.fitness, is_best_species, population_config)

            # Compute the adjusted fitness for this member
            self._individuals[individual_index] = (individual, fitness / n_individuals)

    def _modify_fitness(self, fitness: float, is_best_species: bool, population_config: PopulationSpeciatedConfig):

        # set small fitness if it is absent.
        if fitness == 0.0:
            fitness = 0.0001

        # update the best fitness and stagnation counter
        if fitness >= self._last_best_fitness:
            self._last_best_fitness = fitness
            self.age._no_improvements = 0

        # TODO refactor
        # boost the fitness up to some young age
        number_of_generations = self.age.generations()
        if number_of_generations < population_config.young_age_threshold:
            fitness *= population_config.young_age_fitness_boost

        # penalty for old species
        if number_of_generations > population_config.old_age_threshold:
            fitness *= population_config.old_age_fitness_penalty

        # EXTREME penalty if this species is stagnating for too long time
        # one exception if this is the best species found so far
        if not is_best_species and self.age.no_improvements() > population_config.species_max_stagnation:
            fitness *= 0.0000001

        return fitness

    def create_species(self, new_individuals: List[Individual]) -> Species:
        # create ...
        new_species = Species(new_individuals, self._id, self.age, self._last_best_fitness)
        # TODO study differences in selecting the representative individual.
        new_species._representative = new_individuals[0]  # same as NEAT
        #new_species._representative = self.get_best_individual()

        # TODO next generation

        return new_species

    # ID
    @property
    def id(self) -> int:
        return self._id

    # Individuals
    def append(self, genotype: Genotype):
        self._individuals.append((genotype, None))

    def empty(self):
        return len(self._individuals) == 0

    def __len__(self):
        return len(self._individuals)

    def iter_individuals(self):
        """
        :return: an iterator of (individual, adjusted_fitness) for all individuals of the species
        """
        return iter(self._individuals)

