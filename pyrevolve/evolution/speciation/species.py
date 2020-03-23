from __future__ import annotations
import math

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Optional
    from pyrevolve.evolution.individual import Individual
    from .population_speciated_config import PopulationSpeciatedConfig


class Species:
    def __init__(self, individual: Individual, species_id: int):

        # list of individuals and adjusted fitnesses
        # TODO _adjusted_fitness name to split off from regular individuals
        self._individuals = [(individual, None)]  # type: List[(Individual, Optional[int])]

        # Individual representative of the species
        self._representative: Individual = individual

        # ID of the species
        self._id: int = species_id
        # Age of the species (in generations)
        self._age_generations: int = 0
        # Age of the species (in evaluations)
        self._age_evaluations: int = 0

        self._generations_with_no_improvements: int = 0
        self._last_best_fitness: float = 0.0 # TODO -Inf |-float('Inf')|

    @property
    def id(self) -> int:
        return self._id

    def is_compatible(self,
                      candidate: Individual,
                      population_config: PopulationSpeciatedConfig) -> bool:
        return population_config.are_genomes_compatible(candidate.genotype, self._representative.genotype)

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

    def get_best_fitness(self) -> float:
        """
        Finds the best fitness over all individuals in the species.
        If the species is empty, it returns negative infinity
        :return: the best fitness in the species.
        """
        if self.empty():
            return -math.inf
        # TODO cache?
        return max(self._individuals, key=lambda individual: individual[0].fitness)

    def increase_age_evals(self) -> None:
        self._age_evaluations += 1

    def increase_age_generations(self) -> None:
        self._age_generations += 1

    def increase_gens_no_improvement(self) -> None:
        self._generations_with_no_improvements += 1

    def reset_age_gens(self) -> None:
        self._age_generations = 0
        self._generations_with_no_improvements = 0

    def adjust_fitness(self,
                       is_best_species: bool,
                       population_config: PopulationSpeciatedConfig) -> None:
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

    def next_generation(self, new_individuals: List[Individual]) -> Species:
        # create ...
        new_species = Species(self._representative, self._id)

        new_species._age_evaluations = self._age_evaluations
        new_species._age_generations = self._age_generations
        new_species._


        # TODO make tuple from individuals list
        new_species._individuals = [(individual, None) for individual in new_individuals]
        return new_species
