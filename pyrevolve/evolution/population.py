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
import random
from datetime import datetime
from pathlib import Path
import neat
import gzip


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
                 novelty_on,
                 front,
                 run_simulation,
                 all_settings,
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
        self.novelty_on = novelty_on
        self.front = front
        self.run_simulation = run_simulation
        self.all_settings = all_settings
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
        self.novelty_archive = {}
        for environment in self.conf.environments:
            self.novelty_archive[environment] = []
        self.neat = {'latest_offspring': -1,
                     'latest_snapshot': -1}

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

            if not self.conf.all_settings.use_neat:
                self.conf.experiment_management.export_individual(individual[environment], environment)

        return individual

    async def load_individual(self, id):

        path = 'experiments/'+self.conf.experiment_name+'/data_fullevolution'
        individual = {}
        for environment in self.conf.environments:
            try:
                file_name = os.path.join(path, environment, 'individuals', 'individual_'+id+'.pkl')
                file = open(file_name, 'rb')
                individual[environment] = pickle.load(file)

            except:

                print('bad pickle for robot', id, ' was replaced for new robot with None fitness')
                individual = self._new_individual(
                    self.conf.genotype_constructor(self.conf.genotype_conf, id))

        return individual

    def load_novelty_archive(self):
        path = 'experiments/' + self.conf.experiment_name + '/data_fullevolution'
        file_name = os.path.join(path, 'novelty_archive.pkl')
        if Path(file_name).is_file():
            try:
                file = open(file_name, 'rb')
                self.novelty_archive = pickle.load(file)
            except:
                print('bad pickle for archiive')

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

    def calculate_novelty(self, pool_individuals, environment, gen_num):

        if self.conf.novelty_on['novelty'] or self.conf.novelty_on['novelty_pop']:
            # collecting measures from pop
            pop_measures = []
            self.collect_measures(pool_individuals, pop_measures, environment)

            # pop+archive: complements collection with archive measures
            pop_archive_measures = copy.deepcopy(pop_measures)
            pop_archive_measures = pop_archive_measures + self.novelty_archive[environment]

            pop_measures = np.array(pop_measures)
            pop_archive_measures = np.array(pop_archive_measures)

            if self.conf.novelty_on['novelty']:
                self.calculate_distances(pool_individuals, pop_archive_measures, pop_measures, environment, gen_num, 'pop_archive')
            if self.conf.novelty_on['novelty_pop']:
                self.calculate_distances(pool_individuals, pop_measures, pop_measures, environment, gen_num, 'pop')

            print('> Finished novelty calculation.')

    def calculate_distances(self, pool_individuals, references, to_compare, environment, gen_num, type):
        # calculate distances
        kdt = KDTree(references, leaf_size=30, metric='euclidean')

        # distances from itself and neighbors
        distances, indexes = kdt.query(to_compare, k=self.conf.all_settings.k_novelty+1)

        average_distances = []
        for d in range(0, len(distances)):
            average_distances.append(sum(distances[d])/self.conf.all_settings.k_novelty)

        for i in range(0, len(pool_individuals)):

            if type == 'pop_archive':
                pool_individuals[i][environment].novelty = average_distances[i]
                self.conf.experiment_management.export_novelty(pool_individuals[i][environment], environment, gen_num)
            else:
                pool_individuals[i][environment].novelty_pop = average_distances[i]
                self.conf.experiment_management.export_novelty_pop(pool_individuals[i][environment], environment, gen_num)

    def collect_measures(self, individuals, pop_measures, environment):

        # TODO: get param_measures from a file
        param_measures = [
                          'branching',
                          'limbs',
                          'length_of_limbs',
                          'coverage',
                          'joints',
                          'proportion',
                          'sensors',
                          'symmetry',
                          'size'
                          ]

        for individual in individuals:
            pop_measures.append([])

            for measure in param_measures:
                value = individual[environment].phenotype._morphological_measurements.measurements_to_dict()[measure]
                pop_measures[-1].append(value)

    def update_archive(self, new_individuals):

        # adds random new individuals to the novelty archive
        for environment in self.conf.environments:
            for individual in new_individuals:
                p = random.uniform(0, 1)
                if p < self.conf.all_settings.p_archive:
                    self.collect_measures([individual], self.novelty_archive[environment], environment)

        path = 'experiments/' + self.conf.experiment_name + '/data_fullevolution'
        f = open(f'{path}/novelty_archive.pkl', "wb")
        pickle.dump(self.novelty_archive, f)
        f.close()

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

        # (possibly) run simulation
        if self.conf.run_simulation == 1:
            for environment in self.conf.environments:
                await self.evaluate(new_individuals=self.individuals, gen_num=0, environment=environment)

        # calculate novelty
        for environment in self.conf.environments:
            self.calculate_novelty(self.individuals, environment, gen_num=0)
        self.update_archive(self.individuals)

        # calculate final fitness
        for environment in self.conf.environments:
            self.calculate_final_fitness(individuals=self.individuals, gen_num=0, environment=environment)
        self.consolidate_fitness(self.individuals, gen_num=0)

    async def init_pop_neat(self):
            """
            Populates the population (individuals list) with Individual objects that contains their respective genotype.
            """

            # because we do not have control over neat.reproduction() - with it being all-or-nothing
            # we recover only if all individuals have been reproduced/exported
            # in any case, evaluations do not get lost, because they only happen after reproduction is complete
            if self.neat['latest_offspring'] < 0:

                # initialize
                self.neat['new_cppns_pop'] = self.neat['reproduction'].create_new(self.neat['config'].genome_type,
                                                                                  self.neat['config'].genome_config,
                                                                                  self.conf.population_size)
                # speciate
                self.neat['species'] = self.neat['config'].species_set_type(self.neat['config'].species_set_config,
                                                                            self.neat['reporters'])
                self.neat['species'].speciate(self.neat['config'], self.neat['new_cppns_pop'], generation=0)

                for cppn_individual in self.neat['new_cppns_pop']:

                    genotype = self.conf.genotype_constructor(self.conf.genotype_conf,
                                                              self.neat['new_cppns_pop'][cppn_individual],
                                                              self.next_robot_id)
                    individual = self._new_individual(genotype)
                    # TODO: had to attribute it again to make object mutable, linking refs. should be better though
                    final_season = list(self.conf.environments.keys())[-1]
                    individual[final_season].genotype = genotype

                    self.individuals.append(individual)
                    self.next_robot_id += 1

                for one_species in self.neat['species'].species:
                    for member in self.neat['species'].species[one_species].members:
                        print('member', self.neat['species'].species[one_species].members[member].key,
                              self.neat['species'].species[one_species].members[member].fitness)

                self.neat['latest_offspring'] = 0
                self.save_neat(0)

            # (possibly) run simulation
            if self.conf.run_simulation == 1:
                for environment in self.conf.environments:
                    await self.evaluate(new_individuals=self.individuals, gen_num=0, environment=environment)

            # calculate novelty
            for environment in self.conf.environments:
                self.calculate_novelty(self.individuals, environment, gen_num=0)
            self.update_archive(self.individuals)

            # calculate final fitness for each season
            for environment in self.conf.environments:
                self.calculate_final_fitness(individuals=self.individuals, gen_num=0, environment=environment)

            # consolidate seasonal fitnesses
            self.consolidate_fitness(self.individuals, gen_num=0)

            self.neat['latest_snapshot'] = 0
            self.conf.experiment_management.export_snapshots(self.individuals, 0)
            self.save_neat(0)

    # TODO: find better solution -
    #  pickling this so often is inefficient, but for now i dont trust pickle's address-keeping.
    def save_neat(self, gen_num):
        path = 'experiments/' + self.conf.experiment_name + '/data_fullevolution'
        filename = f'{path}/neat_checkpoint_{gen_num}.pkl'
        with gzip.open(filename, 'w', compresslevel=5) as f:
            data = (self.neat, self.individuals)
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    async def next_gen_neat(self, gen_num):
            """
            Creates next generation of the population through selection, mutation, crossover

            :param gen_num: generation number
            :param individuals: recovered offspring
            :return: new population
            """
            final_season = list(self.conf.environments.keys())[-1]

            if self.neat['latest_offspring'] < gen_num:

                max_id_parents = max(list(self.neat['species'].genome_to_species.keys()))
                self.next_robot_id = max_id_parents+1

                # Create the next generation from the current generation.
                self.neat['new_cppns_pop'] = self.neat['reproduction'].reproduce(self.neat['config'],
                                                                                 self.neat['species'],
                                                                                 self.conf.population_size, gen_num)

                # Check for complete extinction.
                if not self.neat['species'].species:
                        raise Exception("Catastrophe! Extinction!!!")

                # speciate
                self.neat['species'].speciate(self.neat['config'], self.neat['new_cppns_pop'], generation=gen_num)

                all_individuals = []
                new_individuals = 0

                for cppn_individual in self.neat['new_cppns_pop']:

                    if cppn_individual > max_id_parents:

                        genotype = self.conf.genotype_constructor(self.conf.genotype_conf,
                                                                  self.neat['new_cppns_pop'][cppn_individual],
                                                                  self.next_robot_id)
                        individual = self._new_individual(genotype)
                        # TODO: had to attribute it again to make object mutable, linking refs. should be better though
                        individual[final_season].genotype = genotype

                        self.next_robot_id += 1
                        all_individuals.append(individual)
                        new_individuals += 1

                    else:
                        for individual in self.individuals:
                            if int(individual[final_season].genotype.id) == cppn_individual:
                                all_individuals.append(individual)

                self.conf.experiment_management.log_species(gen_num,
                                                            len(self.neat['species'].species),
                                                            len(all_individuals),
                                                            new_individuals)
                self.individuals = all_individuals
                self.neat['latest_offspring'] = gen_num
                self.save_neat(gen_num)

            # (possibly) run simulation
            if self.conf.run_simulation == 1:
                for environment in self.conf.environments:
                    await self.evaluate(new_individuals=self.individuals, gen_num=gen_num, environment=environment)

            # calculate novelty
            for environment in self.conf.environments:
                self.calculate_novelty(self.individuals, environment, gen_num)
            # TODO: do not allow elites to be re-added to archive
            self.update_archive(self.individuals)

            # calculate final fitness
            for environment in self.conf.environments:
                self.calculate_final_fitness(individuals=self.individuals, gen_num=gen_num, environment=environment)

            # consolidate seasonal fitnesses
            self.consolidate_fitness(self.individuals, gen_num)

            new_population = Population(self.conf, self.simulator_queue, self.analyzer_queue, self.next_robot_id)
            new_population.individuals = self.individuals
            new_population.novelty_archive = self.novelty_archive
            new_population.neat = self.neat

            self.neat['latest_snapshot'] = gen_num
            self.conf.experiment_management.export_snapshots(self.individuals, gen_num)
            self.save_neat(gen_num)

            logger.info(f'Population selected in gen {gen_num} with {len(new_population.individuals)} individuals...')

            return new_population

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

        # (possibly) run simulation
        if self.conf.run_simulation == 1:
            for environment in self.conf.environments:
                await self.evaluate(new_individuals=new_individuals, gen_num=gen_num, environment=environment)

        # calculate novelty
        for environment in self.conf.environments:
            self.calculate_novelty(selection_pool, environment, gen_num)
        self.update_archive(new_individuals)

        # calculate final fitness
        for environment in self.conf.environments:
            self.calculate_final_fitness(individuals=selection_pool, gen_num=gen_num, environment=environment)
        self.consolidate_fitness(selection_pool, gen_num)

        # create next population
        if self.conf.population_management_selector is not None:
            new_individuals = self.conf.population_management(selection_pool,
                                                              self.conf.population_management_selector,
                                                              self.conf)
        else:
            new_individuals = self.conf.population_management(self.individuals, new_individuals, self.conf)

        new_population = Population(self.conf, self.simulator_queue, self.analyzer_queue, self.next_robot_id)
        new_population.individuals = new_individuals
        new_population.novelty_archive = self.novelty_archive

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
                logger.info(f'Simulating individual (gen {gen_num}) {individual[environment].genotype.id} ...')
                to_evaluate.append(individual)
                robot_futures.append(asyncio.ensure_future(self.evaluate_single_robot(individual[environment],
                                                                                      environment)))

        await asyncio.sleep(1)

        for i, future in enumerate(robot_futures):
            individual = to_evaluate[i][environment]

            logger.info(f'Simulation of Individual {individual.phenotype.id}')
            individual.phenotype._behavioural_measurements = await future

            if individual.phenotype._behavioural_measurements is None:
                assert (individual.phenotype._behavioural_measurements is None)

            if type_simulation == 'evolve':
                
                individual.evaluated = True
                self.conf.experiment_management.export_behavior_measures(individual.phenotype.id,
                                                                         individual.phenotype._behavioural_measurements,
                                                                         environment)
                if self.conf.all_settings.use_neat:
                    self.save_neat(gen_num)
                else:
                    self.conf.experiment_management.export_individual(individual, environment)

    def calculate_final_fitness(self, individuals, gen_num, environment, type_simulation = 'evolve'):
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        """
        for individual in individuals:

            logger.info(f'Evaluation of Individual {individual[environment].phenotype.id} (gen {gen_num}) ')

            if individual[environment].phenotype._behavioural_measurements is None:
                behavioural_measurements = None
            else:
                behavioural_measurements = individual[environment].phenotype._behavioural_measurements.items()
            conf = copy.deepcopy(self.conf)

            conf.fitness_function = conf.fitness_function[environment]
            individual[environment].fitness =\
                conf.fitness_function(behavioural_measurements, individual[environment])

            logger.info(f'Individual {individual[environment].phenotype.id} has a fitness of {individual[environment].fitness}')

            if type_simulation == 'evolve':
                self.conf.experiment_management.export_fitness(individual[environment], environment, gen_num)

                if not self.conf.all_settings.use_neat:
                    # again, to update and novelty and fitness
                    self.conf.experiment_management.export_individual(individual[environment], environment)

    async def evaluate_single_robot(self, individual, environment):
        """
        :param individual: individual
        :return: Returns future of the evaluation, future returns (fitness, [behavioural] measurements)
        """
        conf = copy.deepcopy(self.conf)

        if self.analyzer_queue is not None:
            collisions, _bounding_box = await self.analyzer_queue.test_robot(individual,
                                                                             conf)
            if collisions > 0:
                logger.info(f"discarding robot {individual} because there are {collisions} self collisions")
                return None

        return await self.simulator_queue[environment].test_robot(individual, conf)

    def consolidate_fitness(self, individuals, gen_num):

        # saves consolidation only in the final season instances of individual (just a convention):
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
                        individual_ref[final_season].consolidated_fitness = 1 / total_masters

                if self.conf.front == 'masters':
                    if masters == 0:
                        individual_ref[final_season].consolidated_fitness = 0
                    else:
                        individual_ref[final_season].consolidated_fitness = 1 / masters

        for individual in individuals:

            self.conf.experiment_management.export_consolidated_fitness(individual[final_season], gen_num)

            if self.conf.all_settings.use_neat:
                fitness = -float('Inf') if individual[final_season].consolidated_fitness is None \
                    else individual[final_season].consolidated_fitness
                individual[final_season].genotype.cppn.fitness = fitness

            else:
                self.conf.experiment_management.export_individual(individual[final_season],
                                                                  final_season)

        print('> Finished fitness consolidation.')

