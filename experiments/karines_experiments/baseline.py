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

async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 2#100
    population_size = 4#100
    offspring_size = 1#50

    # environment world and z-start
    environments = {'plane': 0.03,
                    'tilted5': 0.1
                    }

    genotype_conf = PlasticodingConfig(
        max_structural_modules=15,
        environmental_conditions=['hill'],
        max_terms_clause=1,
        plastic=True,
    )

    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=genotype_conf,
    )

    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
    )
    # experiment params #

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings, environments)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)

    if do_recovery:
        gen_num, has_offspring, next_robot_id = experiment_management.read_recovery_state(population_size,
                                                                                          offspring_size)
        print('fdsngfkdngkfdhbgsdjgnfdsfjgnsdkjfgnsdkjgnsdkhjgbnsdkjhgbskj',gen_num, has_offspring, next_robot_id)

        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0
        next_robot_id = 1

    def fitness_function(robot_manager, robot):
        contacts = measures.contacts(robot_manager, robot)
        assert(contacts != 0)
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
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
        measure_individuals=settings.measure_individuals,
        environments=environments,
    )

    settings = parser.parse_args()

    simulator_queue_envs = {}
    analyzer_queue_envs = {}

    previous_port = None
    # for environment in environments:
    #
    #     settings.world = environment
    #     settings.z_start = environments[environment]
    #
    #     if previous_port is None:
    #         port = settings.port_start
    #         previous_port = port
    #     else:
    #         port = previous_port + settings.n_cores + 1
    #
    #     simulator_queue_envs[environment] = SimulatorQueue(settings.n_cores, settings, port)
    #
    #     await simulator_queue_envs[environment].start()
    #
    #     analyzer_queue_envs[environment] = AnalyzerQueue(1, settings, port+settings.n_cores)
    #    await analyzer_queue_envs[environment].start()

    population = Population(population_conf, simulator_queue_envs, analyzer_queue_envs, next_robot_id)

    if do_recovery:
        # loading a previous state of the experiment
        await population.load_snapshot(gen_num)
        if gen_num >= 0:
            logger.info('Recovered snapshot '+str(gen_num)+', pop with ' + str(len(population.individuals))+' individuals')
        if has_offspring:
            individuals = await population.load_offspring(gen_num, population_size, offspring_size, next_robot_id)
            gen_num += 1
            logger.info('Recovered unfinished offspring '+str(gen_num))

            if gen_num == 0:
                await population.init_pop(individuals)
            else:
                population = await population.next_gen(gen_num, individuals)

            experiment_management.export_snapshots(population.individuals, gen_num)
    else:
        # starting a new experiment
        experiment_management.create_exp_folders()
        await population.init_pop()
        experiment_management.export_snapshots(population.individuals, gen_num)

    sys.exit()
    while gen_num < num_generations-1:
        gen_num += 1
        population = await population.next_gen(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)

    # output result after completing all generations...
