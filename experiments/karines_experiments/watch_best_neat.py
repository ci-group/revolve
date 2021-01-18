#!/usr/bin/env python3
import asyncio

from pyrevolve import parser
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.custom_logging.logger import logger
import sys
import neat
import pprint
import time
import numpy as np


async def run():
    """
    The main coroutine, which is started below.
    """
    # environment world and z-start
    environments = {'plane': 0.03
                    }

    settings = parser.parse_args()

    experiment_management = ExperimentManagement(settings, environments)
    neat_experiment_is_new, neat_checkpoint = experiment_management.neat_experiment_is_new()

    logger.info('Activated run ' + settings.run + ' of experiment ' + settings.experiment_name)

    population_conf = PopulationConfig(
        population_size=None,
        genotype_constructor=None,
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

    simulator_queue = {}
    analyzer_queue = None

    if settings.run_simulation == 1:
        previous_port = None
        for environment in environments:

            settings.world = environment
            settings.z_start = environments[environment]

            if previous_port is None:
                port = settings.port_start
                previous_port = port
            else:
                port = previous_port + settings.n_cores
                previous_port = port

            simulator_queue[environment] = SimulatorQueue(settings.n_cores, settings, port)
            await simulator_queue[environment].start()

        analyzer_queue = AnalyzerQueue(1, settings, port + settings.n_cores)
        await analyzer_queue.start()

    population = Population(population_conf, simulator_queue, analyzer_queue)

    # choose a snapshot here. and the maximum best individuals you wish to watch
    generation = 99
    max_best = 5

    population.individuals = neat_checkpoint['individuals']

    values = []
    for ind in population.individuals:
        # define a criteria here
        for environment in environments:
            ind[environment].evaluated = False
        if ind[list(environments.keys())[-1]].consolidated_fitness is not None:
            values.append(ind[list(environments.keys())[-1]].consolidated_fitness)
        else:
            values.append(-float('Inf'))
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
        print(ind[list(environments.keys())[-1]].phenotype.id, ind[list(environments.keys())[-1]].consolidated_fitness)

    for environment in environments:
        print('watch in ', environment)
        await population.evaluate(new_individuals=population.individuals, gen_num=generation,
                                  environment=environment, type_simulation='watch')
