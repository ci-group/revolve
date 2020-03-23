from __future__ import annotations
from collections.abc import Iterable, Iterator
import math
import numpy

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .population_speciated_config import PopulationSpeciatedConfig
    from pyrevolve.evolution.individual import Individual
    from typing import List, Optional

from pyrevolve.evolution.speciation.species import Species
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
        self._collection = collection if collection is not None else []

        # TODO typing
        # best and worst are a tuple of the index (0) and Individual (1)
        # TODO make elements better accessible.
        self._best = (0, None)
        self._worst = (0, None)

        # TODO different name.
        self._update_prototypes = True

    def __iter__(self) -> SpeciesIterator:
        """
        The __iter__() method returns the iterator object itself, by default we
        return the iterator in ascending order.
        """
        return SpeciesIterator(self._collection)

    def set_individuals(self, species_index, new_individuals):
        self._collection[species_index] = new_individuals
        self._update_prototypes = True

    def get_best(self) -> (int, Species):
        assert len(self._collection) > 0

        if self._update_prototypes:
            """
            :return: the index of the best species
            """
            index = int(
                numpy.argmax(self._collection, key=lambda species: species.get_best_fitness())
            )
            self._best = (index, self._collection[index])
        return self._best

    # TODO refactor function to be smaller.
    def get_worst(self, exclude_empty_species: bool = False) -> (int, Species):
        """
        :return: the index of the worst species and a reference to the worst species
        """
        assert len(self._collection) > 0

        if self._update_prototypes:
            species_iterator = enumerate(iter(self._collection[1:]))

            worst_species_index, worst_species = next(species_iterator)
            worst_species_fitness = worst_species.get_best_fitness()

            while True:
                try:
                    i, species = next(species_iterator)
                except StopIteration:
                    # stop the infinite loop when the iterator is exhausted
                    break

                if not species.empty():
                    species_fitness = species.get_best_fitness()
                else:
                    if exclude_empty_species:
                        # ignore empty species in the loop
                        continue
                    else:
                        species_fitness = -math.inf

                if species_fitness < worst_species_fitness:
                    worst_species_fitness = species_fitness
                    worst_species = species
                    worst_species_index = i

            self._worst = (worst_species_index, worst_species)

        return self._worst

    def add_species(self, item: Species):
        self._collection.append(item)
        self._update_prototypes = True

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
        new_species = []
        for species in self._collection:
            if not species.empty():
                new_species.append(species)

        self._collection = new_species

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


def count_individuals(species_collection: Optional[SpeciesCollection] = None) -> int:
    """
    Counts the number of individuals in the species_list.
    :param species_list: if None, it will use self.species_list
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
