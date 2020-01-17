#!/usr/bin/env python3
import asyncio

from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.tol.manage import measures
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.custom_logging.logger import logger
import sys
import time
import numpy as np

async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 100
    population_size = 100
    offspring_size = 50
    front = 'slaves'

    # environment world and z-start
    environments = {'plane': 0.03,
                    'tilted5': 0.1
                    }

    genotype_conf = PlasticodingConfig(
        max_structural_modules=15,
        plastic=True,
    )

    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=genotype_conf,
    )

    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
    )
    # experiment params #load_individual

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings, environments)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)


    def fitness_function(robot_manager, robot):
        #contacts = measures.contacts(robot_manager, robot)
        #assert(contacts != 0)
        return fitness.displacement_velocity_hill(robot_manager, robot, False)

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function=fitness_function,
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, environments, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection, environments),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
        environments=environments,
        front=front
    )

    settings = parser.parse_args()

    simulator_queue = {}
    analyzer_queue = None

    previous_port = None
    for environment in environments:

        settings.world = environment
        settings.z_start = environments[environment]

        if previous_port is None:
            port = settings.port_start
            previous_port = port
        else:
            port = previous_port+settings.n_cores
            previous_port = port

        simulator_queue[environment] = SimulatorQueue(settings.n_cores, settings, port)
        await simulator_queue[environment].start()

    analyzer_queue = AnalyzerQueue(1, settings, port+settings.n_cores)
    await analyzer_queue.start()

    population = Population(population_conf, simulator_queue, analyzer_queue, 1)

    # choose a snapshot here. and the maximum best individuals you wish to watch
    generation = 61#99
    max_best = 3#10
    await population.load_snapshot(generation)

    values = []
    for ind in population.individuals:
        # define a criteria here
        for environment in environments:
            ind[environment].evaluated = False
        values.append(ind[list(environments.keys())[-1]].consolidated_fitness)
        #values.append(ind['plane'].phenotype._behavioural_measurements.displacement_velocity_hill)

    values = np.array(values)

    ini = len(population.individuals)-max_best
    fin = len(population.individuals)

    population.individuals = np.array(population.individuals)
    # highest
    population.individuals = population.individuals[np.argsort(values)[ini:fin]]
    # lowest
    #population.individuals = population.individuals[np.argsort(values)[0:max_best]]

    for ind in population.individuals:
        print(ind[list(environments.keys())[-1]].phenotype.id)
        print('consolidated_fitness', ind[list(environments.keys())[-1]].consolidated_fitness)

    for environment in environments:
        print(environment)
        await population.evaluate(new_individuals=population.individuals, gen_num=generation,
                                  environment=environment, type_simulation='watch')
