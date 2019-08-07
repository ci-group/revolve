# [(G,P), (G,P), (G,P), (G,P), (G,P)]

from pyrevolve.evolution.individual import Individual
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import measures
from ..custom_logging.logger import logger
from pyrevolve.evolution.learning import Learning
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
                 perform_learning=False,
                 max_learn_evals=None,
                 learn_lamarckian=False,
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
        self.perform_learning = perform_learning
        self.max_learn_evals=max_learn_evals
        self.learn_lamarckian=learn_lamarckian
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
        self.simulator_queue = simulator_queue
        self.analyzer_queue = analyzer_queue
        self.next_robot_id = next_robot_id

    def _new_individual(self, genotype):
        individual = Individual(genotype)
        individual.develop()
        self.conf.experiment_management.export_genotype(individual)
        self.conf.experiment_management.export_phenotype(individual)
        self.conf.experiment_management.export_phenotype_images('data_fullevolution/phenotype_images', individual)
        individual.phenotype.measure_phenotype(self.conf.experiment_name)
        individual.phenotype.export_phenotype_measurements(self.conf.experiment_name)

        return individual

    async def load_individual(self, id):
        path = 'experiments/'+self.conf.experiment_name
        genotype = self.conf.genotype_constructor(self.conf.genotype_conf, id)
        genotype.load_genotype(f'{path}/data_fullevolution/genotypes/genotype_{id}')

        individual = Individual(genotype)
        individual.develop()
        individual.phenotype.measure_phenotype(self.conf.experiment_name)
        
        if os.path.isfile(path+'/data_fullevolution/fitness/fitness_'+id+'.txt'):
            with open(path+'/data_fullevolution/fitness/fitness_'+id+'.txt') as f:
                lines = f.readlines()
                individual.fitness = float(lines[0])

        if os.path.isfile(path+'/data_fullevolution/descriptors/behavior_desc_'+id+'.txt'):
            with open(path+'/data_fullevolution/descriptors/behavior_desc_'+id+'.txt') as f:
                lines = f.readlines()
            individual.phenotype._behavioural_measurements = measures.BehaviouralMeasurements()
            for line in lines:
                if line.split(' ')[0] == 'velocity':
                    individual.phenotype._behavioural_measurements.velocity = float(line.split(' ')[1])
                #if line.split(' ')[0] == 'displacement':
                #   individual.phenotype._behavioural_measurements.displacement = float(line.split(' ')[1])
                if line.split(' ')[0] == 'displacement_velocity':
                    individual.phenotype._behavioural_measurements.displacement_velocity = float(line.split(' ')[1])
                if line.split(' ')[0] == 'displacement_velocity_hill':
                    individual.phenotype._behavioural_measurements.displacement_velocity_hill = float(line.split(' ')[1])
                if line.split(' ')[0] == 'head_balance':
                    individual.phenotype._behavioural_measurements.head_balance = float(line.split(' ')[1])
                if line.split(' ')[0] == 'contacts':
                    individual.phenotype._behavioural_measurements.contacts = float(line.split(' ')[1])

        return individual

    async def load_snapshot(self, gen_num):
        """
        Recovers all genotypes and fitnesses of robots in the lastest selected population
        :param gen_num: number of the generation snapshot to recover
        """
        path = 'experiments/'+self.conf.experiment_name
        for r, d, f in os.walk(path +'/selectedpop_'+str(gen_num)):
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

        self.next_robot_id = next_robot_id
        return individuals

    async def init_pop(self, recovered_individuals=[]):
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        for i in range(self.conf.population_size-len(recovered_individuals)):
            individual = self._new_individual(self.conf.genotype_constructor(self.conf.genotype_conf, self.next_robot_id))
            self.individuals.append(individual)
            self.next_robot_id += 1

        await self.evaluate(self.individuals, 0)
        self.individuals = recovered_individuals + self.individuals

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
                child_genotype = self.conf.crossover_operator(parents, self.conf.genotype_conf, self.conf.crossover_conf)
                child = Individual(child_genotype)
            else:
                child = self.conf.selection(self.individuals)

            child.genotype.id = self.next_robot_id
            self.next_robot_id += 1

            # Mutation operator
            child_genotype = self.conf.mutation_operator(child.genotype, self.conf.mutation_conf)
            # Insert individual in new population
            individual = self._new_individual(child_genotype)

            new_individuals.append(individual)

        # evaluate new individuals
        await self.evaluate(new_individuals, gen_num)

        new_individuals = recovered_individuals + new_individuals

        # create next population
        if self.conf.population_management_selector is not None:
            new_individuals = self.conf.population_management(self.individuals, new_individuals,
                                                              self.conf.population_management_selector)
        else:
            new_individuals = self.conf.population_management(self.individuals, new_individuals)
        new_population = Population(self.conf, self.simulator_queue, self.analyzer_queue, self.next_robot_id)
        new_population.individuals = new_individuals
        logger.info(f'Population selected in gen {gen_num} with {len(new_population.individuals)} individuals...')

        return new_population

    async def evaluate(self, new_individuals, gen_num, type_simulation = 'evolve', learn_eval=False):
        """
        Evaluates each individual in the new gen population

        :param new_individuals: newly created population after an evolution iteration
        :param gen_num: generation number
        """
        # Parse command line / file input arguments
        # await self.simulator_connection.pause(True)
        robot_futures = []
        for individual in new_individuals:
            logger.info(f'Evaluating individual (gen {gen_num}) {individual.genotype.id} ...')
            robot_futures.append(asyncio.ensure_future(self.evaluate_single_robot(individual, gen_num, learn_eval)))


        await asyncio.sleep(1)

        for i, future in enumerate(robot_futures):
            individual = new_individuals[i]
            logger.info(f'Evaluation of Individual {individual.phenotype.id}')
            individual.fitness, individual.phenotype._behavioural_measurements = await future
            
            if individual.phenotype._behavioural_measurements is None:
                assert (individual.fitness is None)
            elif type_simulation == 'evolve':
                self.conf.experiment_management.export_behavior_measures(individual.phenotype.id, individual.phenotype._behavioural_measurements)
                self.conf.experiment_management.write_to_speed_file(individual.phenotype.id, individual.phenotype._behavioural_measurements)

            if type_simulation == 'evolve':
                self.conf.experiment_management.export_fitness(individual)
                self.conf.experiment_management.write_to_fitness_file(individual.phenotype.id, individual.fitness)
                logger.info(f' Individual {individual.phenotype.id} has a fitness of {individual.fitness}')
                
                        
    async def evaluate_single_robot(self, individual, gen_num, learn_eval=False):
        if individual.phenotype is None:
                individual.develop()

        if self.analyzer_queue is not None and not learn_eval:
            collisions, _bounding_box = await self.analyzer_queue.test_robot(individual, self.conf)
            if collisions > 0:
                logger.info(f"discarding robot {individual} because there are {collisions} self collisions")
                return None, None

        #perform learning
        if self.conf.perform_learning and not learn_eval:
            individual = await self.learn(individual, gen_num)

        return await self.simulator_queue.test_robot(individual, self.conf)

    async def learn(self, individual, gen_num):
        """
        Learn individual by cma
        :param individual:
        :param gen_num:
        """
        # check if individual has not been learned before or has unfinished learning
        if not self.conf.experiment_management.has_finished_learning(individual.phenotype.id):
            learn_brain = Learning(individual, gen_num, self.simulator_queue, self.conf, population=self)
            learn_brain.learn_counter = self.conf.experiment_management.learning_iterations_performed(individual.phenotype.id, gen_num) + 1
            individual = await learn_brain.learn_brain_through_cma_es()
            
            self.conf.experiment_management.export_fitness(individual)
            self.conf.experiment_management.export_behavior_measures(individual.phenotype.id, individual.phenotype._behavioural_measurements)
            self.conf.experiment_management.finished_learning(individual.phenotype.id)
        
        return individual
