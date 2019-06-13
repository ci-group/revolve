# [(G,P), (G,P), (G,P), (G,P), (G,P)]

from pyrevolve.evolution.individual import Individual
from pyrevolve.SDF.math import Vector3
from ..custom_logging.logger import logger
import time
import asyncio
import os


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
                 measure_individuals,
                 offspring_size=None,
                 next_robot_id=0):
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
        :param measure_individuals: weather or not to perform  phenotypic measurements
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
        self.measure_individuals = measure_individuals
        self.offspring_size = offspring_size
        self.next_robot_id = next_robot_id


class Population:
    def __init__(self, conf: PopulationConfig, simulator_connection, next_robot_id):
        """
        Creates a Population object that initialises the
        individuals in the population with an empty list
        and stores the configuration of the system to the
        conf variable.

        :param conf: configuration of the system
        :param simulator_connection: connection to the simulator
        :param next_robot_id: (sequential) id of the next individual to be created
        """
        self.conf = conf
        self.individuals = []
        self.simulator_connection = simulator_connection
        self.next_robot_id = next_robot_id

    def _new_individual(self, genotype):
        individual = Individual(genotype)
        individual.develop()
        self.conf.experiment_management.export_genotype(individual)
        self.conf.experiment_management.export_phenotype(individual)
        self.conf.experiment_management.export_phenotype_images('data_fullevolution/phenotype_images', individual)
        if self.conf.measure_individuals:
            individual.phenotype.measure_phenotype(self.conf.experiment_name)

        return individual

    async def load_pop(self, gen_num):
        path = 'experiments/'+self.conf.experiment_name
        for r, d, f in os.walk(path +'/selectedpop_'+str(gen_num)):
            for file in f:
                if 'body' in file:
                    genotype_id = file.split('.')[0].split('_')[-1]
                    genotype = self.conf.genotype_constructor(self.conf.genotype_conf, genotype_id)
                    genotype.load_genotype(f'{path}/data_fullevolution/genotypes/genotype_{genotype_id}.txt')

                    individual = Individual(genotype)
                    individual.develop()

                    with open(path+'/data_fullevolution/fitness/fitness_'+genotype_id+'.txt') as f:
                        lines = f.readlines()
                        individual.fitness = float(lines[0])

                    self.individuals.append(individual)

    async def init_pop(self):
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        for i in range(self.conf.population_size):
            individual = self._new_individual(self.conf.genotype_constructor(self.conf.genotype_conf, self.next_robot_id))
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)
        self.conf.experiment_management.export_fitnesses(self.individuals)

    async def next_gen(self, gen_num):
        """
        Creates next generation of the population through selection, mutation, crossover

        :param gen_num: generation number

        :return: new population
        """

        new_individuals = []

        for _i in range(self.conf.offspring_size):
            # Selection operator (based on fitness)
            # Crossover
            if self.conf.crossover_operator is not None:
                parents = self.conf.parent_selection(self.individuals)
                child = self.conf.crossover_operator(parents, self.conf.genotype_conf, self.conf.crossover_conf)
            else:
                child = self.conf.selection(self.individuals)

            child.id = self.next_robot_id
            child.genotype.id = self.next_robot_id
            self.next_robot_id += 1

            # Mutation operator
            child_genotype = self.conf.mutation_operator(child.genotype, self.conf.mutation_conf)
            # Insert individual in new population
            individual = self._new_individual(child_genotype)
            new_individuals.append(individual)

        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)
        self.conf.experiment_management.export_fitnesses(new_individuals)

        # create next population
        if self.conf.population_management_selector is not None:
            new_individuals = self.conf.population_management(self.individuals, new_individuals,
                                                              self.conf.population_management_selector)
        else:
            new_individuals = self.conf.population_management(self.individuals, new_individuals)
        new_population = Population(self.conf, self.simulator_connection, self.next_robot_id)
        new_population.individuals = new_individuals

        return new_population

    async def evaluate(self, new_individuals, gen_num):
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution itertation
        :param gen_num: generation number
        """
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        robot_futures = []
        for individual in new_individuals:
            logger.info(f'Evaluating individual (gen {gen_num}) {individual.genotype.id} ...')
            robot_futures.append(self.evaluate_single_robot(individual))

        await asyncio.sleep(1)

        for i, future in enumerate(robot_futures):
            individual = new_individuals[i]
            logger.info(f'Evaluation of Individual {individual.phenotype.id}')
            individual.fitness = await future
            logger.info(f'Evaluation complete! Individual {individual.phenotype.id} has a fitness of {individual.fitness}')

    def evaluate_single_robot(self, individual):
        if individual.phenotype is None:
            individual.develop()
        return self.simulator_connection.test_robot(individual.phenotype, self.conf)
