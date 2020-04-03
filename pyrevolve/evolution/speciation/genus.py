from __future__ import annotations

from pyrevolve.custom_logging.logger import logger
from .species import Species
from .species_collection import SpeciesCollection, count_individuals

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .population_speciated_config import PopulationSpeciatedConfig
    from pyrevolve.evolution.individual import Individual
    from typing import List, Callable, Iterator, Coroutine, Optional


class Genus:
    """
    Collection of species
    """

    def __init__(self,
                 config: PopulationSpeciatedConfig,
                 species_collection: Optional[SpeciesCollection] = None,
                 next_species_id: int = 1):
        """
        Creates the genus object.
        :param config: Population speciated config.
        :param species_collection: Managers the list of species.
        """
        #TODO refactor config (is it part of species, species collection, or genus?
        self.config: PopulationSpeciatedConfig = config

        self.species_collection: SpeciesCollection = SpeciesCollection() \
            if species_collection is None else species_collection

        self._next_species_id: int = next_species_id

    def __len__(self):
        return len(self.species_collection)

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
            # Iterate through each species and check if compatible. If compatible, then add the species.
            # If not compatible, create a new species.
            for species in self.species_collection:
                if species.is_compatible(individual, self.config):
                    species.append(individual)
                    break
            else:
                self.species_collection.add_species(Species([individual], self._next_species_id))
                self._next_species_id += 1

        self.species_collection.cleanup()

    async def next_generation(self,
                              recovered_individuals: List[Individual],
                              generate_individual_function: Callable[[List[Individual]], Individual],
                              evaluate_individuals_function: Callable[[List[Individual]], Coroutine]) -> Genus:
        """
        Creates the genus for the next generation

        :param recovered_individuals: TODO implement recovery
        :param generate_individual_function: The function that generates a new individual.
        :param evaluate_individuals_function: Function to evaluate new individuals
        :return: The Genus of the next generation
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
        need_evaluation: List[Individual] = []
        orphans: List[Individual] = []
        old_species_individuals: List[List[Individual]] = [[] for _ in range(len(self.species_collection))]

        ##################################################################
        # GENERATE NEW INDIVIDUALS
        for species_index, species in enumerate(self.species_collection):

            # Get the individuals from the individual with adjusted fitness tuple list.
            old_species_individuals[species_index] = [individual for individual, _ in species.iter_individuals()]

            new_individuals = []

            for _ in range(offspring_amounts[species_index]):
                new_individual = generate_individual_function(old_species_individuals[species_index])
                need_evaluation.append(new_individual)

                # if the new individual is compatible with the species, otherwise create new.
                if species.is_compatible(new_individual, self.config):
                    new_individuals.append(new_individual)
                else:
                    orphans.append(new_individual)

            new_species_collection.add_species(species.create_species(new_individuals))

        ##################################################################
        # MANAGE ORPHANS, POSSIBLY CREATE NEW SPECIES
        # recheck if other species can adopt the orphan individuals.
        for orphan in orphans:
            for species in new_species_collection:
                if species.is_compatible(orphan, self.config):
                    species.append(orphan)
                    break
            else:
                new_species_collection.add_species(Species([orphan], self._next_species_id))
                # add an entry for new species which does not have a previous iteration.
                self._next_species_id += 1

        # Do a recount on the number of offspring per species.
        offspring_amounts = self._count_offsprings(self.config.population_size - len(orphans))

        ##################################################################
        # EVALUATE NEW INDIVIDUALS
        # TODO avoid recovered individuals here [partial recovery]
        await evaluate_individuals_function(need_evaluation)

        ##################################################################
        # POPULATION MANAGEMENT
        # Update the species population, based on the population management algorithm.
        for species_index, new_species in enumerate(new_species_collection):
            new_species_individuals = [individual for individual, _ in new_species.iter_individuals()]

            if species_index >= len(old_species_individuals):
                # Finished. The new species keep the entire population.
                break

            # create next population ## Same as population.next_gen
            new_individuals = self.config.population_management(new_species_individuals,
                                                                old_species_individuals[species_index],
                                                                offspring_amounts[species_index],
                                                                self.config.population_management_selector)
            new_species.set_individuals(new_individuals)

        ##################################################################
        # ASSERT SECTION
        # check species IDs [complicated assert]
        species_id = set()
        for species in new_species_collection:
            if species.id in species_id:
                raise RuntimeError(f"Species ({species.id}) present twice")
            species_id.add(species.id)

        new_species_collection.cleanup()

        # Assert species list size and number of individuals
        n_individuals = count_individuals(new_species_collection)
        if n_individuals != self.config.population_size:
            raise RuntimeError(f'count_individuals(new_species_collection) = {n_individuals} != '
                               f'{self.config.population_size} = population_size')

        ##################################################################
        # Create the next GENUS
        new_genus = Genus(self.config, new_species_collection, self._next_species_id)

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
        sum_species_offspring_amount = sum(species_offspring_amount)

        if sum_species_offspring_amount != number_of_individuals:
            raise RuntimeError(f'generated sum_species_offspring_amount ({sum_species_offspring_amount}) '
                               f'does not equal number_of_individuals ({number_of_individuals}).\n'
                               f'species_offspring_amount: {species_offspring_amount}')

        return species_offspring_amount

    def _calculate_average_fitness(self, number_of_individuals: int) -> float:
        # Calculate the total adjusted fitness
        total_adjusted_fitness: float = 0.0
        for species in self.species_collection:
            for _, adjusted_fitness in species.iter_individuals():
                total_adjusted_fitness += adjusted_fitness

        # Calculate the average adjusted fitness
        assert total_adjusted_fitness > 0.0
        average_adjusted_fitness = total_adjusted_fitness / float(number_of_individuals)

        return average_adjusted_fitness

    def _calculate_population_size(self, average_adjusted_fitness: float) -> List[int]:
        species_offspring_amount: List[int] = []

        for species in self.species_collection:
            offspring_amount: float = 0.0
            for individual, adjusted_fitness in species.iter_individuals():
                offspring_amount += adjusted_fitness / average_adjusted_fitness
            # sometimes offspring amount could become `numpy.float64` which will break the code becuause it cannot
            # be used in ranges. Forcing conversion to integers here fixes that issue.
            species_offspring_amount.append(int(round(offspring_amount)))

        return species_offspring_amount

    def _correct_population_size(self, species_offspring_amount: List[int], missing_offspring: int) -> List[int]:
        if missing_offspring > 0:  # positive have lacking individuals
            # take best species and
            species_offspring_amount[self.species_collection.get_best()[0]] += missing_offspring

        elif missing_offspring < 0:  # negative have excess individuals
            # remove missing number of individuals
            remove_offspring = -missing_offspring  # get the positive number of individual to remove
            worst_species_index, _ = self.species_collection.get_worst(remove_offspring)
            species_offspring_amount[worst_species_index] -= remove_offspring

        return species_offspring_amount
