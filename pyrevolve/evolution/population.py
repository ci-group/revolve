# [(G,P), (G,P), (G,P), (G,P), (G,P)]

from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution import fitness
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import measures
from ..custom_logging.logger import logger
from sklearn.neighbors import KDTree
import numpy as np
import time
import asyncio
import copy
import os
import pickle
import sys
from random import random


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
                 environments,
                 front,
                 run_simulation,
                 offspring_size=None,
                 next_robot_id=1):
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
        self.environments = environments
        self.front = front
        self.run_simulation = run_simulation
        self.offspring_size = offspring_size
        self.next_robot_id = next_robot_id


class Population:

    def __init__(self, conf: PopulationConfig, simulator_queue, analyzer_queue=None, next_robot_id=1):
        """
        Creates a Population object that initialises the
        individuals in the population with an empty list
        and stores the configuration of the system to the
        conf variable.

        :param conf: configuration of the system
        :param simulator_queue: connection to the simulator queue
        :param analyzer_queue: connection to the analyzer simulator queue
        :param next_robot_id: (sequential) id of the next individual to be created
        """
        self.conf = conf
        self.individuals = []
        self.analyzer_queue = analyzer_queue
        self.simulator_queue = simulator_queue
        self.next_robot_id = next_robot_id

    def _new_individual(self, genotype):

        individual = {}
        individual_temp = Individual(genotype)

        for environment in self.conf.environments:

            individual[environment] = copy.deepcopy(individual_temp)
            individual[environment].develop(environment)

            if len(individual) == 1:
                self.conf.experiment_management.export_genotype(individual[environment])

        for environment in self.conf.environments:

            self.conf.experiment_management.export_phenotype(individual[environment], environment)
            self.conf.experiment_management.export_phenotype_images(os.path.join('data_fullevolution',
                                                                    environment,'phenotype_images'),
                                                                    individual[environment])
            individual[environment].phenotype.measure_phenotype(self.conf.experiment_name)
            individual[environment].phenotype.export_phenotype_measurements(self.conf.experiment_name, environment)
            # because of the bloating in plasticoding, cleans up intermediate phenotype before saving object
            individual[environment].genotype.intermediate_phenotype = None
            self.conf.experiment_management.export_individual(individual[environment], environment)

        return individual

    async def load_individual(self, id):
        path = 'experiments/'+self.conf.experiment_name+'/data_fullevolution'

        individual = {}
        for environment in self.conf.environments:
            try:
                file_name = os.path.join(path, environment,'individuals','individual_'+id+'.pkl')
                file = open(file_name, 'rb')
                individual[environment] = pickle.load(file)
            except EOFError:
                print('bad pickle for robot', id, ' was replaced for new robot with None fitness')
                individual = self._new_individual(
                        self.conf.genotype_constructor(self.conf.genotype_conf, id))

        return individual

    async def load_snapshot(self, gen_num):
        """
        Recovers all genotypes and fitnesses of robots in the latest selected population
        :param gen_num: number of the generation snapshot to recover
        """
        final_season = list(self.conf.environments.keys())[-1]
        path = 'experiments/'+self.conf.experiment_name
        for r, d, f in os.walk(os.path.join(path,'selectedpop_'+
                               final_season,'selectedpop_'+str(gen_num))):
            for file in f:
                if 'body' in file:
                    id = file.split('.')[0].split('_')[-2]+'_'+file.split('.')[0].split('_')[-1]
                    self.individuals.append(await self.load_individual(id))

    async def load_offspring(self, last_snapshot, population_size, offspring_size, next_robot_id):
        """
        Recovers the part of an unfinished offspring
        :param
        :return:
        """
        individuals = []
        # number of robots expected until the latest snapshot
        if last_snapshot == -1:
            n_robots = 0
        else:
            n_robots = population_size + last_snapshot * offspring_size

        for robot_id in range(n_robots+1, next_robot_id):
            individuals.append(await self.load_individual('robot_'+str(robot_id)))

        return individuals

    def consolidate_fitness(self, individuals):
        # saves consolidation only in the final season instances of individual:
        final_season = list(self.conf.environments.keys())[-1]

        if len(self.conf.environments) == 1:
            for individual in individuals:
                fit = individual[final_season].fitness
                individual[final_season].consolidated_fitness = fit

        # if there are multiple seasons (environments)
        else:
            for individual_ref in individuals:

                slaves = 0
                total_slaves = 0
                total_masters = 0
                masters = 0

                # this BIZARRE logic works only for two seasons! shame on me! fix it later!
                for individual_comp in individuals:

                    equal = 0
                    better = 0

                    for environment in self.conf.environments:
                        if individual_ref[environment].fitness is None \
                                and individual_comp[environment].fitness is None:
                            equal += 1

                        if individual_ref[environment].fitness is None \
                                and individual_comp[environment].fitness is not None:
                            equal += -1

                        if individual_ref[environment].fitness is not None \
                                and individual_comp[environment].fitness is None:
                            better += 1

                        if individual_ref[environment].fitness is not None \
                                and individual_comp[environment].fitness is not None:

                            if individual_ref[environment].fitness > individual_comp[environment].fitness:
                                better += 1

                            if individual_ref[environment].fitness < individual_comp[environment].fitness:
                                equal += -1

                            if individual_ref[environment].fitness == individual_comp[environment].fitness:
                                equal += 1

                    # if it ref is not worse in any objective, and better in at least one, the comp becomes slave of ref
                    if equal >= 0 and better > 0:
                        slaves += 1

                    # if better in all objectives
                    if better == len(self.conf.environments):
                        total_slaves += 1

                    # if it is totally worse
                    if equal < 0 and better == 0:
                        total_masters += 1

                    # if it is worse
                    if equal <= 0 and better == 0:
                        masters += 1

                if self.conf.front == 'slaves':
                    individual_ref[final_season].consolidated_fitness = slaves

                if self.conf.front == 'total_slaves':
                    individual_ref[final_season].consolidated_fitness = total_slaves

                if self.conf.front == 'total_masters':
                    if total_masters == 0:
                        individual_ref[final_season].consolidated_fitness = 0
                    else:
                        individual_ref[final_season].consolidated_fitness = 1/total_masters

                if self.conf.front == 'masters':
                    if masters == 0:
                        individual_ref[final_season].consolidated_fitness = 0
                    else:
                        individual_ref[final_season].consolidated_fitness = 1/masters

        for individual in individuals:
            self.conf.experiment_management.export_consolidated_fitness(individual[final_season])

            self.conf.experiment_management.export_individual(individual[final_season],
                                                                final_season)

    def calculate_novelty(self, individuals):

        # saves novelty only in the final season instances of individual:
        final_season = list(self.conf.environments.keys())[-1]

        # TODO: get param_measures from a file
        param_measures = ['branching',
                          'limbs',
                          'length_of_limbs',
                          'coverage',
                          'joints',
                          'proportion'
                          ,'sensors',
                          'symmetry',
                          'size'
                          ]
        # neighbors
        k = 3
        ##

        # collecting measures from pop
        pop_measures = []
        for individual in individuals:
            pop_measures.append([])

            for measure in param_measures:
                value = individual[final_season].phenotype._morphological_measurements.measurements_to_dict()[measure]
                pop_measures[-1].append(value)

        # collecting measures from pop+arquive
        pop_arquive_measures = copy.deepcopy(pop_measures)
        # TODO: complements with archive measures
        #pop_arquive_measures.append([])

        pop_measures = np.array(pop_measures)
        pop_arquive_measures = np.array(pop_arquive_measures)

        print(pop_measures)
        print(pop_arquive_measures)

        # calculate distances
        kdt = KDTree(pop_arquive_measures, leaf_size=30, metric='euclidean')

        # distances from itself and neighbors
        distances, indexes = kdt.query(pop_measures, k=k+1)
        print(indexes)
        print(distances)

        average_distances = []
        for d in range(0, len(distances)):
            average_distances.append(sum(distances[d])/k)

        print(average_distances)

        for i in range(0, len(individuals)):
            individuals[i][final_season].novelty = average_distances[i]
            self.conf.experiment_management.export_novelty(individuals[i][final_season])

    async def init_pop(self, recovered_individuals=[]):
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        for i in range(self.conf.population_size-len(recovered_individuals)):
            individual = self._new_individual(
                self.conf.genotype_constructor(self.conf.genotype_conf, self.next_robot_id))

            self.individuals.append(individual)
            self.next_robot_id += 1

        self.individuals = recovered_individuals + self.individuals

        self.calculate_novelty(self.individuals)

        if self.conf.run_simulation == 1:
            for environment in self.conf.environments:
                await self.evaluate(new_individuals=self.individuals, gen_num=0, environment=environment)
        else:
            for environment in self.conf.environments:
                await self.evaluate_non_simulated(new_individuals=self.individuals, gen_num=0, environment=environment)

        self.consolidate_fitness(self.individuals)

    async def next_gen(self, gen_num, recovered_individuals=[]):
        """
        Creates next generation of the population through selection, mutation, crossover

        :param gen_num: generation number
        :param individuals: recovered offspring
        :return: new population
        """

        new_individuals = []

        for _i in range(self.conf.offspring_size-len(recovered_individuals)):
            # Selection operator (based on fitness)
            # Crossover
            if self.conf.crossover_operator is not None:
                parents = self.conf.parent_selection(self.individuals)
                child_genotype = self.conf.crossover_operator(self.conf.environments,
                                                              parents,
                                                              self.conf.genotype_conf,
                                                              self.conf.crossover_conf)
                child = Individual(child_genotype)
            else:
                child = self.conf.selection(self.individuals)

            child.genotype.id = self.next_robot_id
            self.next_robot_id += 1

            # Mutation operator
            child_genotype = self.conf.mutation_operator(child.genotype,
                                                         self.conf.mutation_conf)

            # Insert individual in new population
            individual = self._new_individual(child_genotype)
            new_individuals.append(individual)

        new_individuals = recovered_individuals + new_individuals
        selection_pool = self.individuals + new_individuals

        self.calculate_novelty(selection_pool)

        # evaluate new individuals
        if self.conf.run_simulation == 1:
            for environment in self.conf.environments:
                await self.evaluate(new_individuals=new_individuals, gen_num=gen_num, environment=environment)
        else:
            for environment in self.conf.environments:
                await self.evaluate_non_simulated(new_individuals=new_individuals, gen_num=gen_num, environment=environment)

        self.consolidate_fitness(selection_pool)

        # create next population
        if self.conf.population_management_selector is not None:
            new_individuals = self.conf.population_management(selection_pool,
                                                              self.conf.population_management_selector,
                                                              self.conf)
        else:
            new_individuals = self.conf.population_management(self.individuals, new_individuals, self.conf)

        new_population = Population(self.conf, self.simulator_queue, self.analyzer_queue, self.next_robot_id)
        new_population.individuals = new_individuals

        logger.info(f'Population selected in gen {gen_num} with {len(new_population.individuals)} individuals...')

        return new_population

    async def evaluate(self, new_individuals, gen_num, environment, type_simulation = 'evolve'):
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        """
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        robot_futures = []
        to_evaluate = []
        for individual in new_individuals:
            if not individual[environment].evaluated:
                logger.info(f'Evaluating individual (gen {gen_num}) {individual[environment].genotype.id} ...')
                to_evaluate.append(individual)
                robot_futures.append(asyncio.ensure_future(self.evaluate_single_robot(individual[environment],
                                                                                      environment)))
                individual[environment].evaluated = True

        await asyncio.sleep(1)

        for i, future in enumerate(robot_futures):
            individual = to_evaluate[i][environment]

            logger.info(f'Evaluation of Individual {individual.phenotype.id}')
            individual.fitness, individual.phenotype._behavioural_measurements = await future

            if individual.phenotype._behavioural_measurements is None:
                assert (individual.fitness is None)

            if type_simulation == 'evolve':
                self.conf.experiment_management.export_behavior_measures(individual.phenotype.id,
                                                                         individual.phenotype._behavioural_measurements,
                                                                         environment)

            logger.info(f'Individual {individual.phenotype.id} has a fitness of {individual.fitness}')
            if type_simulation == 'evolve':
                self.conf.experiment_management.export_fitness(individual, environment)
                self.conf.experiment_management.export_individual(individual, environment)

    async def evaluate_non_simulated(self, new_individuals, gen_num, environment, type_simulation = 'evolve'):
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        """
        for individual in new_individuals:

            logger.info(f'Evaluation of Individual {individual[environment].phenotype.id} (gen {gen_num}) ')

            conf = copy.deepcopy(self.conf)
            conf.fitness_function = conf.fitness_function[environment]
            individual[environment].fitness = conf.fitness_function(None, individual[environment])

            if type_simulation == 'evolve':
                self.conf.experiment_management.export_behavior_measures(individual[environment].phenotype.id,
                                                                         individual[environment].phenotype._behavioural_measurements,
                                                                         environment)

            logger.info(f'Individual {individual[environment].phenotype.id} has a fitness of {individual[environment].fitness}')
            if type_simulation == 'evolve':
                self.conf.experiment_management.export_fitness(individual[environment], environment)
                self.conf.experiment_management.export_individual(individual[environment], environment)

    async def evaluate_single_robot(self, individual, environment):
        """
        :param individual: individual
        :return: Returns future of the evaluation, future returns (fitness, [behavioural] measurements)
        """

        conf = copy.deepcopy(self.conf)
        conf.fitness_function = conf.fitness_function[environment]

        if self.analyzer_queue is not None:
            collisions, _bounding_box = await self.analyzer_queue.test_robot(individual,
                                                                             conf)
            if collisions > 0:
                logger.info(f"discarding robot {individual} because there are {collisions} self collisions")
                return None, None

        return await self.simulator_queue[environment].test_robot(individual, conf)