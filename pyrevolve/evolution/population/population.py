
from pyrevolve.evolution.individual import Individual
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.individual import create_individual


class PopulationConfig:
    def __init__(self,
                 population_size: int,
                 genotype_constructor,
                 genotype_conf,
                 fitness_function,
                 mutation_operator,
                 mutation_conf,
                 crossover_operator,
                 crossover_conf,
                 selection,
                 parent_selection,
                 population_management,
                 population_management_selector,
                 evaluation_time,
                 experiment_name,
                 experiment_management,
                 offspring_size=None):
        """
        Creates a PopulationConfig object that sets the particular configuration for the population

        :param population_size: size of the population
        :param genotype_constructor: class of the genotype used
        :param genotype_conf: configuration for genotype constructor
        :param fitness_function: function that takes in a `RobotManager` as a parameter and produces a fitness for the robot
        :param mutation_operator: operator to be used in mutation
        :param mutation_conf: configuration for mutation operator
        :param crossover_operator: operator to be used in crossover
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

    def __init__(self, config: PopulationConfig, individuals = None):
        """
        Creates a Population object that initialises the
        individuals in the population with an empty list
        and stores the configuration of the system to the
        conf variable.

        :param config: configuration of the system
        """
        self.config = config

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


def create_population(config, previous_population, new_individuals, generation_index):
    if config.population_management_selector is not None:
        new_individuals = config.population_management(previous_population.individuals, new_individuals,
                                                            config.population_management_selector)
    else:
        new_individuals = config.population_management(previous_population.individuals, new_individuals)

    new_population = Population(config, new_individuals)
    logger.info(f'Population selected in gen {generation_index} with {len(new_population.individuals)} individuals...')

    return new_population
