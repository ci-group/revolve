from __future__ import annotations
from collections.abc import Iterable, Iterator
import math
import numpy
from pyrevolve.evolution.speciation.species import Species
from pyrevolve.evolution.individual import Individual

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Optional, Set
    from .population_speciated_config import PopulationSpeciatedConfig
    from pyrevolve.evolution.individual import Individual


"""
Based on https://refactoring.guru/design-patterns/iterator/python/example
To create an iterator in Python, there are two abstract classes from the built-
in `collections` module - Iterable,Iterator. 
method in the iterator.
"""


class SpeciesCollection(Iterable):
    """
    Concrete Collections provide one or several methods for retrieving fresh
    iterator instances, compatible with the collection class.
    """

    def __init__(self, collection: List[Species] = None) -> None:
        self._collection: List[Species] \
            = collection if collection is not None else []

        # CACHING ELEMENTS
        # best and worst are a tuple of the index (0) and Individual (1)
        # TODO make elements better accessible.
        self._best: (int, Species) = (0, None)
        #self._worst: (int, Species) = (0, None)

        self._cache_needs_updating: bool = True

    def __iter__(self) -> SpeciesIterator:
        """
        The __iter__() method returns the iterator object itself, by default we
        return the iterator in ascending order.
        """
        return SpeciesIterator(self._collection)

    def set_individuals(self, species_index: int, new_individuals: List[Individual]) -> None:
        self._collection[species_index].set_individuals(new_individuals)
        self._cache_needs_updating = True

    def _update_cache(self) -> None:
        assert len(self._collection) > 0

        # BEST
        species_best_fitness = [species.get_best_individual().fitness for species in self._collection]
        species_best_fitness = map(lambda f: -math.inf if f is None else f, species_best_fitness)
        index = int(numpy.argmax(species_best_fitness))
        self._best = (index, self._collection[index])

        # cannot calculate WORST cache, because
        # there are 2 different version of the worst individual.
        # Which one should be cached?

        self._cache_needs_updating = False

    def get_best(self) -> (int, Species):
        """
        :return: the index of the best species and the species
        """
        assert len(self._collection) > 0

        if self._cache_needs_updating:
            self._update_cache()
        return self._best

    def get_worst(self,
                  minimal_size: int,
                  exclude_id_list: Optional[Set[int]] = None) -> (int, Species):
        """
        Finds the worst species (based on the best fitness of that species)
        Crashes if there are no species with at least `minimal_size` individuals

        :param minimal_size: Species with less individuals than this will not be considered
        :param exclude_id_list: Species in this list will be ignored
        :return: the index and a reference to the worst species
        """
        assert len(self._collection) > 0

        worst_species_index, worst_species = self._calculate_worst_fitness(minimal_size, exclude_id_list)

        assert worst_species_index != -1
        assert worst_species is not None

        return worst_species_index, worst_species

    def _calculate_worst_fitness(self,
                                 minimal_size: int,
                                 exclude_id_list: Optional[Set[int]]) -> (int, Species):
        worst_species_index = -1
        worst_species_fitness = math.inf
        worst_species = None

        for i, species in enumerate(self._collection):

            if exclude_id_list is not None \
                    and species.id in exclude_id_list:
                continue

            if len(species) < minimal_size:
                continue
                # TODO remove - this is never used since the function is only called in count_offsprings.
                # species_fitness = -math.inf

            species_fitness = species.get_best_fitness()
            species_fitness = -math.inf if species_fitness is None else species_fitness
            if species_fitness < worst_species_fitness:
                worst_species_fitness = species_fitness
                worst_species = species
                worst_species_index = i

        return worst_species_index, worst_species

    def add_species(self, item: Species):
        self._collection.append(item)
        self._cache_needs_updating = True

    def __len__(self):
        """
        Get the length of the species
        :return: number of species
        """
        return len(self._collection)

    def cleanup(self) -> None:
        """
        Remove all empty species (cleanup routine for every case..)
        """
        new_collection = []
        for species in self._collection:
            if not species.empty():
                new_collection.append(species)

        self._collection = new_collection

    def clear(self) -> None:
        self._collection.clear()

    def adjust_fitness(self, config: PopulationSpeciatedConfig) -> None:
        """
        Computes the adjusted fitness for all species
        """
        for species in self._collection:
            species.adjust_fitness(species is self.get_best()[1], config)

    def update(self) -> None:
        """
        Updates the best_species, increases age for all species
        """
        # the old best species will be None at the first iteration
        _, old_best_species = self.get_best()

        for species in self._collection:
            # Reset the species and update its age
            species.age.increase_generations()
            species.age.increase_no_improvement()

        # This prevents the previous best species from sudden death
        # If the best species happened to be another one, reset the old
        # species age so it still will have a chance of survival and improvement
        # if it grows old and stagnates again, it is no longer the best one
        # so it will die off anyway.
        if old_best_species is not None:
            old_best_species.age.reset_generations()


def count_individuals(species_collection: SpeciesCollection) -> int:
    """
    Counts the number of individuals in the species_list.
    :param species_collection: collection of species
    :return: the total number of individuals
    """
    # count the total number of individuals inside every species in the species_list
    number_of_individuals = 0

    for species in species_collection:
        number_of_individuals += len(species)

    return number_of_individuals


class SpeciesIterator(Iterator):
    """
    Concrete Iterators implement various traversal algorithms. These classes
    store the current traversal position at all times.
    """

    """
    `_position` stores the current traversal position.
    """
    _position: int = None

    def __init__(self, collection: List[Species]) -> None:
        self._collection = collection
        self._position = 0

    def __next__(self):
        """
        The __next__() method must return the next item in the sequence. On
        reaching the end, and in subsequent calls, it must raise StopIteration.
        """
        try:
            value = self._collection[self._position]
            self._position += 1
        except IndexError:
            raise StopIteration()

        return value


if __name__ == "__main__":
    from pyrevolve.genotype.genotype import Genotype
    # The client code may or may not know about the Concrete Iterator or
    # Collection classes, depending on the level of indirection you want to keep
    # in your program.
    collection = SpeciesCollection()
    individual1 = Individual(Genotype())
    collection.add_species(Species([individual1], 0))
    individual2 = Individual(Genotype())
    collection.add_species(Species([individual2], 1))
    individual3 = Individual(Genotype())
    collection.add_species(Species([individual3], 2))

    print("Straight traversal:")
    for individual in collection:
        print(individual)
    print("")
