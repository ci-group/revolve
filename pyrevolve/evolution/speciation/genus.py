
import copy
import numpy

from .species import Species
from .population_speciated_config import PopulationSpeciatedConfig


class Genus:

    def __init__(self, config : PopulationSpeciatedConfig):
        self.config = config

        self.species_list = []
        self._next_species_id = 0
        self._best_species = None

    def speciate(self, species_list):

        assert len(individuals) > 0

        # clear out the species list
        species_list.clear()

        # NOTE: we are comparing the new generation's genomes to the representatives from the previous generation!
        # Any new species that is created is assigned a representative from the new generation.
        for individual in individuals:
            genome = individual.genotype
            # Iterate through each species and check if compatible. If compatible, then add the species.
            # If not compatible, create a new species.
            # TODO maybe restructure with individual instead of genome...
            for species in self.species_list:
                if species.is_compatible(genome, self.config):
                    species.append(genome)
                    break
            else:
                self.species_list.append(
                    Species(individual, self._next_species_id)
                )
                self._next_species_id += 1

        self._cleanup_species()

    def _cleanup_species(self):
        """
        Remove all empty species (cleanup routine for every case..)
        """
        new_species = []
        for species in self.species_list:
            if not species.empty():
                new_species.append(species)

        self.species_list = new_species

    def next_generation(self, recovered_individuals, generate_individual_function):
        # update species stagnation and stuff
        self._update_species()

        # update adjusted fitnesses
        self._adjust_fitness()

        # calculate offspring amount
        offspring_amounts = self._count_offsprings(self.config.offspring_size)

        # clone species:
        new_species_list = []
        orphans = []

        # Generate new individuals
        for species, offspring_amount in zip(self.species_list, offspring_amounts):

            # Get the individuals from the individual with adjusted fitness tuple list.
            species_individuals = [individual for individual, _ in species.iter_individuals()]

            new_individuals = []

            #TODO offspring amount: ???
            for _ in range(offspring_amount):
                new_individual = generate_individual_function(species_individuals)

                # if the new individual is compatible with the species, otherwise create new.
                if species.is_compatible(new_individual.genome, self.config):
                    new_individuals.append(new_individual)
                else:
                    orphans.append(new_individual)

            new_species_list.append(species.next_generation(new_individuals))

        # create new species from orphans
        for orphan in orphans:
            for species in new_species_list:
                if species.is_compatible(orphan.genome, self.config):
                    new_species_list.append(orphan)
                    break
            else:
                new_species_list.append(Species(orphan, self._next_species_id))
                self._next_species_id += 1

        offspring_amounts = self._count_offsprings(self.config.population_size)

        # TODO finish up population management.
        for species, offspring_amount in zip(self.species_list, offspring_amounts):
            species_individuals = [individual for individual, _ in species.iter_individuals()]
            # create next population ## Same as population.next_gen
            # TODO new individuals
            new_individuals = self.config.population_management(species_individuals, new_individuals,
                                                                offspring_amount, self.config.population_management_selector)

        #TODO assert species list size and number of individuals
        assert(self.config.population_size == number_of_individuals(new_species_list))

        new_genus = Genus(self.config)
        new_genus.species_list = new_species_list
        new_genus._cleanup_species()

        return new_genus

    def _update_species(self):
        # the old best species will be None at the first iteration
        old_best_species = self._best_species

        # Mark the best species so it is guaranteed to survive.
        self._best_species = max(self.species_list, key=lambda species: species.get_best_fitness())

        for species in self.species_list:
            # Reset the species and update its age
            species.increase_age_generations()
            species.increase_gens_no_improvement()
            # TODO remove (how many of this species should be spawned for the next population)
            species.SetOffspringRqd(0)

        # This prevents the previous best species from sudden death
        # If the best species happened to be another one, reset the old
        # species age so it still will have a chance of survival and improvement
        # if it grows old and stagnates again, it is no longer the best one
        # so it will die off anyway.
        if old_best_species is not None:
            old_best_species.reset_age_gens()

    def _adjust_fitness(self):
        for species in self.species_list:
            species.adjust_fitness(species is self._best_species, self.config)



    # TODO testing
    # TODO list of all individuals for all species
    def _count_offsprings(self, number_of_individuals):

        assert number_of_individuals > 0

        total_adjusted_fitness = 0.0

        for species in self.species_list:
            for _, adjusted_fitness in species.iter_individuals():
                total_adjusted_fitness += adjusted_fitness

        assert total_adjusted_fitness > 0.0

        average_adjusted_fitness = total_adjusted_fitness / float(number_of_individuals)

        species_offspring_amount = [] # list of integers
        for species in self.species_list:
            offspring_amount = 0.0
            for individual, adjusted_fitness in species.iter_individuals():
                offspring_amount += adjusted_fitness / average_adjusted_fitness
            species_offspring_amount.append(round(offspring_amount))

        total_offspring_amount = sum(species_offspring_amount)

        missing = number_of_individuals - total_offspring_amount

        if missing > 0: # positive have lacking individuals
            # TODO take best species
            species_offspring_amount[self._best_species_index()] += missing

        elif missing < 0: # negative have excess individuals
            # TODO remove missing number of individuals
            # TODO more documentation ...
            # TODO check if the number of individuals is not smaller than 1
            species_offspring_amount[self._worst_species_index()] -= -missing

        # There are some individuals missing from approximation
        #missing_offsprings = self.config.offspring_size - len(new_individuals)

        #assert missing_offsprings >= 0
        #best_species = self.species_list[0]  # TODO call best species
        #for _ in range(missing_offsprings):
        #    species_individuals = [individual for individual, _ in best_species.iter_individuals()]
        #    generate_individual_function(species_individuals)


        return species_offspring_amount

    #TODO performance of double finding.
    def _best_species_index(self):
        return numpy.argmax(self.species_list, key=lambda species: species.get_best_fitness())

    def _worst_species(self):
        return numpy.sort(self.species_list, key=lambda species: species.get_best_fitness())

def number_of_individuals(species_list):
    # count the total number of individuals inside every species in the species_list
    number_of_individuals = 0
    for species in species_list:
        number_of_individuals += len(species._individuals)  # todo function number of individuals.
    return number_of_individuals