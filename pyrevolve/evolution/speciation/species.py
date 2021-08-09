from __future__ import annotations
import math
import os
import yaml

from pyrevolve.evolution.speciation.age import Age

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Optional, Dict, Iterator, Callable
    from pyrevolve.evolution.individual import Individual
    from .population_speciated_config import PopulationSpeciatedConfig


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

        # ID of the species
        self._id: int = species_id

        self.age: Age = Age() if age is None else age

        # Fitness
        self._last_best_fitness: float = best_fitness  # TODO -Inf |-float('Inf')|

    def __eq__(self, other):
        if not isinstance(other, Species):
            # don't attempt to compare against unrelated types
            return NotImplemented

        if self._id != other._id or self.age != other.age:
            return False

        for (individual1, fit1), (individual2, fit2) in zip(self._individuals, other._individuals):
            if individual1 != individual2 or fit1 != fit2:
                return False
        return True

    # TODO refactor population_config
    def is_compatible(self, candidate: Individual, population_config: PopulationSpeciatedConfig) -> bool:
        """
        Tests if the candidate individual is compatible with this Species
        :param candidate: candidate individual to test against the current species
        :param population_config: config where to pick the `are genomes compatible` function
        :return: if the candidate individual is compatible or not
        """
        if self.empty():
            return False
        return population_config.are_individuals_compatible(candidate, self._representative())

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
        return max(self._individuals,
                   key=lambda individual: individual[0].fitness if individual[0].fitness is not None else -math.inf)[0]

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
            fitness = individual.fitness
            if fitness is None:
                fitness = 0.0
            assert fitness >= 0.0  # TODO can we make this work with negative fitnesses?

            fitness = self._adjusted_fitness(fitness, is_best_species, population_config)

            # Compute the adjusted fitness for this member
            self._individuals[individual_index] = (individual, fitness / n_individuals)

    def _adjusted_fitness(self,
                          fitness: float,
                          is_best_species: bool,
                          population_config: PopulationSpeciatedConfig) -> float:
        """
        Generates the adjusted fitness (not normalized) for the individual.
        It's based on its current fitness, the status of the species and the Configuration of the experiment.

        It also updates the self._last_best_fitness.

        :param fitness: real fitness of the individual
        :param is_best_species: is `self` the best species in the population?
        :param population_config: experimental configuration
        :return: the adjusted fitness for the individual (not normalized)
        """
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
        """
        Clone the current species with a new list of individuals.
        This function is necessary to produce the new generation.

        Updating the age of the species should have already been happened before this.
        This function will not update the age.

        :param new_individuals: list of individuals that the cloned species should have
        :return: The cloned Species
        """
        return Species(new_individuals, self._id, self.age, self._last_best_fitness)

    # ID
    @property
    def id(self) -> int:
        return self._id

    def _representative(self) -> Individual:
        """
        Returns a reference to the representative individual.
        It crashes if the species is empty.
        :return: the representative individual
        """
        # TODO study differences in selecting the representative individual.
        return self._individuals[0][0]
        # return self.get_best_individual()

    # Individuals
    def append(self, individual: Individual) -> None:
        self._individuals.append((individual, None))

    def empty(self) -> bool:
        return len(self._individuals) == 0

    def __len__(self):
        return len(self._individuals)

    def iter_individuals(self) -> Iterator[(Individual, float)]:
        """
        :return: an iterator of (individual, adjusted_fitness) for all individuals of the species
        """
        return iter(self._individuals)

    def serialize(self, filename: str) -> None:
        """
        Saving the Species to file in yaml formats.
        :param filename: file where to save the species
        """
        data = {
            'id': self.id,
            'individuals_ids': [int(individual.id) for individual, _ in self._individuals],
            'age': self.age.serialize()
        }

        with open(filename, 'w') as file:
            yaml.dump(data, file)

    @staticmethod
    def Deserialize(filename: str,
                    loaded_individuals: Dict[int, Individual],
                    load_individual_fn: Callable[[int], Individual] = None) -> Species:
        """
        Alternative constructor that loads the species from file
        :param filename: path to the species file
        :param loaded_individuals: dictionary of all individuals ever created, to get a reference of them into
          inside loaded_individuals list
        :param load_individual_fn: optional function to load up individuals from disk
        :return: loaded Species
        """
        assert os.path.isfile(filename)
        with open(filename, 'r') as file:
            data = yaml.load(file, Loader=yaml.SafeLoader)

        def read_or_load(_id: int) -> Individual:
            if load_individual_fn is not None and _id not in loaded_individuals:
                loaded_individuals[_id] = load_individual_fn(_id)
            return loaded_individuals[_id]

        individuals = [read_or_load(_id) for _id in data['individuals_ids']]

        species = Species(
            individuals=individuals,
            species_id=data['id'],
        )
        species.age = Age.Deserialize(data['age'])

        return species

    def set_individuals(self, new_individuals: List[Individual]):
        self._individuals = [(individual, None) for individual in new_individuals]
