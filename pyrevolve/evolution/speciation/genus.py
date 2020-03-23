from __future__ import annotations

import copy
import math
import numpy
from .species import Species

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .population_speciated_config import PopulationSpeciatedConfig
    from pyrevolve.evolution.individual import Individual
    from typing import List, Optional, Callable, Iterator
    from pyrevolve.evolution.speciation.species_collection import SpeciesCollection, number_of_individuals


class Genus:
    """
    Collection of species
    """

    def __init__(self, config: PopulationSpeciatedConfig, species_collection: SpeciesCollection = SpeciesCollection()):
        """
        Creates the genus object.
        :param config: Population speciated config.
        :param species_collection: Managers the list of species.
        """
        self.config: PopulationSpeciatedConfig = config
        self.species_collection: SpeciesCollection = species_collection
        self._next_species_id: int = 0

    def iter_individuals(self) -> Iterator[Individual]:
        """
        :return: an iterator of `individual` for all individuals of the species
        """
        for species in self.species_collection:
            for individual, _ in species.iter_individuals():
                yield individual

    # TODO refactor
    def speciate(self, individuals: List[Individual]) -> None:
        """
        Creates the species. It takes a list of individuals and splits them into multiple species, grouping the
        compatible individuals together.

        :param individuals:
        :return:
        """
        assert len(individuals) > 0

        # clear out the species list
        self.species_collection.clear()

        # NOTE: we are comparing the new generation's genomes to the representatives from the previous generation!
        # Any new species that is created is assigned a representative from the new generation.
        for individual in individuals:
            genotype = individual.genotype
            # Iterate through each species and check if compatible. If compatible, then add the species.
            # If not compatible, create a new species.
            # TODO maybe restructure with individual instead of genome...
            for species in self.species_collection:
                if species.is_compatible(genotype, self.config):
                    species.append(genotype)
                    break
            else:
                self.species_collection.add_species(Species(individual, self._next_species_id))
                self._next_species_id += 1

        self.species_collection.cleanup()

    def next_generation(self,
                        recovered_individuals: List[Individual],
                        generate_individual_function: Callable[[List[Individual]], Individual]) -> Genus:
        """
        Creates the genus for the next generation

        :param recovered_individuals: TODO implement recovery
        :param generate_individual_function: The function that generates a new individual.
        :return:
        """
        assert len(recovered_individuals) == 0

        # update species stagnation and stuff
        self.species_collection.update()

        # update adjusted fitnesses
        self.species_collection.adjust_fitness(self.config)

        # calculate offspring amount
        offspring_amounts = self._count_offsprings(self.config.offspring_size)

        # clone species:
        new_species_collection = SpeciesCollection()
        orphans: List[Individual] = []

        # Generate new individuals
        for species, offspring_amount in zip(self.species_collection, offspring_amounts):

            # Get the individuals from the individual with adjusted fitness tuple list.
            species_individuals = [individual for individual, _ in species.iter_individuals()]

            new_individuals = []

            #TODO offspring amount: ???
            for _ in range(offspring_amount):
                new_individual = generate_individual_function(species_individuals)

                # if the new individual is compatible with the species, otherwise create new.
                if species.is_compatible(new_individual.genotype, self.config):
                    new_individuals.append(new_individual)
                else:
                    orphans.append(new_individual)

            new_species_collection.add_species(species.next_generation(new_individuals))

        # create new species from orphans
        #TODO refactor
        for orphan in orphans:
            for species in new_species_collection:
                if species.is_compatible(orphan.genotype, self.config):
                    species.append(orphan)
                    break
            else:
                new_species_collection.add_species(Species(orphan, self._next_species_id))
                self._next_species_id += 1

        offspring_amounts = self._count_offsprings(self.config.population_size)

        # TODO finish up population management.
        for species, offspring_amount in zip(self.species_collection, offspring_amounts):
            species_individuals = [individual for individual, _ in species.iter_individuals()]
            # create next population ## Same as population.next_gen
            # TODO new individuals
            new_individuals = self.config.population_management(species_individuals, new_individuals,
                                                                offspring_amount, self.config.population_management_selector)

        #TODO assert species list size and number of individuals
        assert(self.config.population_size == number_of_individuals(new_species_collection))

        new_genus = Genus(self.config, new_species_collection)
        new_genus.species_collection.cleanup()

        return new_genus

    # TODO testing
    # TODO list of all individuals for all species
    def _count_offsprings(self, number_of_individuals: int) -> List[int]:
        """
        Calculates the number of offspring allocated for each individual.
        The total of allocated individuals will be `number_of_individuals`

        :param number_of_individuals: Total number of individuals to generate.
        :return: a list of integers representing the number of allocated individuals for each species.
        The index of this list correspond to the same index in self._species_list.
        """
        assert number_of_individuals > 0

        total_adjusted_fitness = 0.0

        for species in self.species_collection:
            for _, adjusted_fitness in species.iter_individuals():
                total_adjusted_fitness += adjusted_fitness

        assert total_adjusted_fitness > 0.0

        average_adjusted_fitness = total_adjusted_fitness / float(number_of_individuals)

        species_offspring_amount = [] # list of integers
        for species in self.species_collection:
            offspring_amount = 0.0
            for individual, adjusted_fitness in species.iter_individuals():
                offspring_amount += adjusted_fitness / average_adjusted_fitness
            species_offspring_amount.append(round(offspring_amount))

        total_offspring_amount = sum(species_offspring_amount)

        missing = number_of_individuals - total_offspring_amount

        if missing > 0: # positive have lacking individuals
            # TODO take best species
            species_offspring_amount[self.species_collection.get_best()[0]] += missing

        elif missing < 0: # negative have excess individuals
            # TODO remove missing number of individuals
            # TODO more documentation ...
            species_offspring_amount[self.species_collection.get_worst(exclude_empty_species=True)[0]] -= -missing

        # There are some individuals missing from approximation
        #missing_offsprings = self.config.offspring_size - len(new_individuals)

        #assert missing_offsprings >= 0
        #best_species = self.species_list[0]  # TODO call best species
        #for _ in range(missing_offsprings):
        #    species_individuals = [individual for individual, _ in best_species.iter_individuals()]
        #    generate_individual_function(species_individuals)

        return species_offspring_amount
