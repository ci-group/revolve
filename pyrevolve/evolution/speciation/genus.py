from __future__ import annotations

from .species import Species

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .population_speciated_config import PopulationSpeciatedConfig
    from pyrevolve.evolution.individual import Individual
    from typing import List, Optional, Callable, Iterator
    from pyrevolve.evolution.speciation.species_collection import SpeciesCollection, count_individuals


class Genus:
    """
    Collection of species
    """

    def __init__(self, config: PopulationSpeciatedConfig, species_collection: SpeciesCollection = None):
        """
        Creates the genus object.
        :param config: Population speciated config.
        :param species_collection: Managers the list of species.
        """
        #TODO refactor config (is it part of species, species collection, or genus?
        self.config: PopulationSpeciatedConfig = config

        self.species_collection: SpeciesCollection = SpeciesCollection() \
            if species_collection is None else species_collection

        self._next_species_id: int = 0

    def iter_individuals(self) -> Iterator[Individual]:
        """
        Returns all individuals from the species.
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
                self.species_collection.add_species(Species([individual], self._next_species_id))
                self._next_species_id += 1

        self.species_collection.cleanup()

    def next_generation(self, recovered_individuals: List[Individual],
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
        old_species_individuals: List[List[Individual]] = [[] for _ in range(len(self.species_collection))]

        # Generate new individuals
        for species_index, species in enumerate(self.species_collection):

            # Get the individuals from the individual with adjusted fitness tuple list.
            old_species_individuals[species_index] = [individual for individual, _ in species.iter_individuals()]

            new_individuals = []

            for _ in range(offspring_amounts[species_index]):
                new_individual = generate_individual_function(old_species_individuals[species_index])

                # if the new individual is compatible with the species, otherwise create new.
                if species.is_compatible(new_individual.genotype, self.config):
                    new_individuals.append(new_individual)
                else:
                    orphans.append(new_individual)

            new_species_collection.set_individuals(species_index, species.create_species(new_individuals))

        # recheck if other species can adopt the orphan individuals.
        for orphan in orphans:
            for species in new_species_collection:
                if species.is_compatible(orphan.genotype, self.config):
                    species.append(orphan)
                    break
            else:
                new_species_collection.add_species(Species([orphan], self._next_species_id))
                # add an entry for new species which does not have a previous iteration.
                old_species_individuals.append([])
                self._next_species_id += 1

        # Do a recount on the number of offspring per species.
        offspring_amounts = self._count_offsprings(self.config.population_size)

        # Update the species population, based on the population management algorithm.
        for species_index, species in enumerate(self.species_collection):
            species_individuals = [individual for individual, _ in species.iter_individuals()]
            # create next population ## Same as population.next_gen
            new_individuals = self.config.population_management(species_individuals,
                                                                old_species_individuals[species_index],
                                                                offspring_amounts[species_index],
                                                                self.config.population_management_selector)
            new_species_collection.set_individuals(species_index, new_individuals)

        new_species_collection.cleanup()

        # Assert species list size and number of individuals
        assert count_individuals(new_species_collection) == self.config.population_size

        new_genus = Genus(self.config, new_species_collection)

        return new_genus

    # TODO testing
    # TODO separate these functions to a different class, and pass on the species collection.
    def _count_offsprings(self, number_of_individuals: int) -> List[int]:
        """
        Calculates the number of offspring allocated for each individual.
        The total of allocated individuals will be `number_of_individuals`

        :param number_of_individuals: Total number of individuals to generate.
        :return: a list of integers representing the number of allocated individuals for each species.
        The index of this list correspond to the same index in self._species_list.
        """
        assert number_of_individuals > 0

        average_adjusted_fitness: float = self._calculate_average_fitness(number_of_individuals)

        species_offspring_amount: List[int] = self._calculate_population_size(average_adjusted_fitness)

        missing_offspring = number_of_individuals - sum(species_offspring_amount)

        species_offspring_amount = self._correct_population_size(species_offspring_amount, missing_offspring)

        return species_offspring_amount

    def _calculate_average_fitness(self, number_of_individuals: int) -> float:
        # Calculate the total adjusted fitness
        total_fitness: float = 0.0
        for species in self.species_collection:
            for _, fitness in species.iter_individuals():
                total_fitness += fitness

        assert total_fitness > 0.0
        average_adjusted_fitness = total_fitness / float(number_of_individuals)

        return average_adjusted_fitness

    def _calculate_population_size(self, average_adjusted_fitness) -> List[int]:
        species_offspring_amount: List[int] = []

        for species in self.species_collection:
            offspring_amount: float = 0.0
            for individual, adjusted_fitness in species.iter_individuals():
                offspring_amount += adjusted_fitness / average_adjusted_fitness
            species_offspring_amount.append(round(offspring_amount))

        return species_offspring_amount

    def _correct_population_size(self, species_offspring_amount, missing_offspring) -> List[int]:
        
        if missing_offspring > 0:  # positive have lacking individuals
            # take best species and
            species_offspring_amount[self.species_collection.get_best()[0]] += missing_offspring

        elif missing_offspring < 0:  # negative have excess individuals
            # remove missing number of individuals
            remove_offspring = -missing_offspring  # get the positive number of individual to remove
            worst_species_index, _ = self.species_collection.get_worst(remove_offspring)
            species_offspring_amount[worst_species_index] -= remove_offspring

        return species_offspring_amount
