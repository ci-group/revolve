from __future__ import annotations

from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.individual import create_individual

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyrevolve.evolution.individual import Individual
    from pyrevolve.genotype import Genotype
    from typing import Callable, Optional, List
    from pyrevolve.revolve_bot import RevolveBot
    from pyrevolve.tol.manage.robotmanager import RobotManager
    from typing import List, Optional
    from pyrevolve.util.generation import Generation


class PopulationConfig:

    def __init__(self, population_size: int,
                 genotype_constructor: Callable[[object, int], Genotype],
                 genotype_conf: object,
                 fitness_function: Callable[[RobotManager, RevolveBot], float],
                 mutation_operator: Callable[[Genotype, object], Genotype],
                 mutation_conf: object,
                 crossover_operator: Callable[[List[Individual], object, object], Genotype],
                 crossover_conf: object,
                 selection: Callable[[List[Individual]], Individual],
                 parent_selection: Callable[[List[Individual]], List[Individual]],
                 population_management: Callable[
                    [List[Individual], List[Individual], Callable[[List[Individual]], Individual]],
                    List[Individual]
                 ],
                 population_management_selector: Callable[[List[Individual]], Individual],
                 evaluation_time: float,
                 experiment_name: str,
                 experiment_management,
                 offspring_size: Optional[int] = None):
        """
        Creates a PopulationConfig object that sets the particular configuration for the population

        :param population_size: size of the population
        :param genotype_constructor: class of the genotype used.
            First parameter is the config of the genome.
            Second is the id of the genome
        :param genotype_conf: configuration for genotype constructor
        :param fitness_function: function that takes in a `RobotManager` as a parameter and produces a fitness for the robot
        :param mutation_operator: operator to be used in mutation
        :param mutation_conf: configuration for mutation operator
        :param crossover_operator: operator to be used in crossover.
            First parameter is the list of parents (usually 2).
            Second parameter is the Genotype Conf
            Third parameter is Crossover Conf
        :param selection: selection type
        :param parent_selection: selection type during parent selection
        :param population_management: type of population management ie. steady state or generational
        :param evaluation_time: duration of an experiment
        :param experiment_name: name for the folder of the current experiment
        :param experiment_management: object with methods for managing the current experiment
        :param offspring_size (optional): size of offspring (for steady state)
        """
        self.population_size = population_size
        self.genotype_constructor = genotype_constructor
        self.genotype_conf = genotype_conf
        self.fitness_function = fitness_function
        self.mutation_operator = mutation_operator
        self.mutation_conf = mutation_conf
        self.crossover_operator = crossover_operator
        self.crossover_conf = crossover_conf
        self.parent_selection = parent_selection
        self.selection = selection
        self.population_management = population_management
        self.population_management_selector = population_management_selector
        self.evaluation_time = evaluation_time
        self.experiment_name = experiment_name
        self.experiment_management = experiment_management
        self.offspring_size = offspring_size


class Population:

    def __init__(self, config: PopulationConfig, individuals: List[Individual] = None):

        """
        Creates a Population object that initialises the
        individuals in the population with an empty list
        and stores the configuration of the system to the
        conf variable.

        :param config: configuration of the system
        """
        self.config: PopulationConfig = config

        if individuals is None:
            self.individuals = []
        else:
            self.individuals = individuals

    def evolve(self, recovered_individuals):
        new_individuals = []

        for _i in range(self.config.offspring_size - len(recovered_individuals)):
            # Selection operator (based on fitness)
            # Crossover
            if self.config.crossover_operator is not None:
                parents = self.config.parent_selection(self.individuals)
                child_genotype = self.config.crossover_operator(parents, self.config.genotype_conf,
                                                                self.config.crossover_conf)
                child = Individual(child_genotype)
            else:
                child = self.config.selection(self.individuals)

            # Mutation operator
            child_genotype = self.config.mutation_operator(child.genotype, self.config.mutation_conf)
            # Insert individual in new population
            individual = create_individual(self.config.experiment_management, child_genotype)

            new_individuals.append(individual)

        return new_individuals


# Factory method for population
def create_population(previous_population: Population, new_individuals):
    if previous_population.config.population_management_selector is not None:
        new_individuals = previous_population.config.population_management(previous_population.individuals, new_individuals,
                                                            previous_population.config.population_management_selector)
    else:
        new_individuals = previous_population.config.population_management(previous_population.individuals, new_individuals)

    new_population = Population(previous_population.config, new_individuals)
    logger.info(f'Population selected in gen {Generation.getInstance().index()} with {len(new_population.individuals)} individuals...')

    return new_population

