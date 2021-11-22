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
    settings = parser.parse_args()
    # environment world and z-start
    if 'staticplane' in settings.experiment_name:
        environments = {'plane': 0.1}
    elif 'statictilted' in settings.experiment_name:
        environments = {'tilted5': 0.1}
    else:
        environments = {'unique': 0.1}

    experiment_management = ExperimentManagement(settings, environments)

    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)

    population_conf = PopulationConfig(
        population_size=None,
        genotype_constructor=random_initialization,
        genotype_conf=None,
        fitness_function=None,
        mutation_operator=None,
        mutation_conf=None,
        crossover_operator=None,
        crossover_conf=None,
        selection=None,
        parent_selection=None,
        population_management=None,
        population_management_selector=None,
        evaluation_time=settings.evaluation_time,
        offspring_size=None,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
        environments=environments,
        novelty_on=None,
        front=None,
        run_simulation=settings.run_simulation,
        all_settings=settings,
    )

    settings = parser.parse_args()

    simulator_queue = {}
    analyzer_queue = None

    if settings.run_simulation == 1:
        previous_port = None
        for environment in environments:
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
    generation = settings.watch_gen
    max_best = settings.watch_k
    await population.load_snapshot(generation)

    values = []
    for ind in population.individuals:
        # define a criteria here
        for environment in environments:
            ind[environment].evaluated = False
            
        if ind[list(environments.keys())[-1]].consolidated_fitness is not None:
            values.append(ind[list(environments.keys())[-1]].consolidated_fitness)
            #values.append(ind[list(environments.keys())[-1]].phenotype._behavioural_measurements.displacement_velocity_hill)
        else:
            values.append(-float('Inf'))
    values = np.array(values)
    population.individuals = np.array(population.individuals)
    # highest
    population.individuals = population.individuals[np.argsort(-1*values)]
    # lowest
    #population.individuals = population.individuals[np.argsort(values)]

    to_eval = []
    for idx, ind in enumerate(population.individuals):
        # if population.individuals[idx][list(environments.keys())[-1]].phenotype.id \
        #         in ('robot_3026', 'robot_3039', 'robot_3067', 'robot_3072', 'robot_3021', 'robot_3216'):
        if True:
            to_eval.append(population.individuals[idx])
    to_eval = to_eval[0:max_best]

    for idx,ind in enumerate(to_eval):
        print(ind[list(environments.keys())[-1]].phenotype.id, ind[list(environments.keys())[-1]].consolidated_fitness)#,
              #ind[list(environments.keys())[-1]].phenotype._behavioural_measurements.displacement_velocity_hill)

    for environment in environments:
        print('watch in', environment)
        await population.evaluate(new_individuals=to_eval, gen_num=generation,
                                  environment=environment, type_simulation=settings.watch_type)

# ./revolve.py --manager experiments/karines_experiments/alifejournal21/watch_robust.py --evaluation-time 50 --simulator-cmd gazebo --watch-k 1 --watch-gen 99 --world tilted5 --experiment-name link_storage/alifej2021/scaffeq_4