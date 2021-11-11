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
    num_generations = 100
    population_size = 100
    offspring_size = 50
    front = 'none'

    # calculation of the measures can be on or off, because they are expensive
    novelty_on = {'novelty': False,
                  'novelty_pop': True,
                  'measures': ['branching',
                               'limbs',
                               'length_of_limbs',
                               'coverage',
                               'joints',
                               'proportion',
                               'symmetry']
                  }

    genotype_conf = PlasticodingConfig(
        max_structural_modules=15,
        plastic=False,
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

    # instance of phenotype (it does not have plasticity, so uses a dummy one)
    # it is internally called environment
    instances_phenotype = {'unique': None}

    experiment_management = ExperimentManagement(settings, instances_phenotype)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)

    if do_recovery:
        gen_num, has_offspring, next_robot_id = experiment_management.read_recovery_state(population_size,
                                                                                          offspring_size)

        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0
        next_robot_id = 1

    # same fitness for all levels of inclination
    def fitness_function_plane(measures, robot):
        return fitness.displacement_velocity_hill(measures, robot)

    fitness_function = {list(instances_phenotype.keys())[-1]: fitness_function_plane}

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function=fitness_function,
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, instances_phenotype, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection, instances_phenotype),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
        environments=instances_phenotype,
        novelty_on=novelty_on,
        front=front,
        run_simulation=settings.run_simulation,
        all_settings=settings,
    )

    simulator_queue = {}
    analyzer_queue = None

    if settings.run_simulation == 1:
        previous_port = None

        for instance_phenotype in instances_phenotype:
            settings.z_start = 0.1
            # just as a remainder! :D
            settings.world = settings.world

            if previous_port is None:
                port = settings.port_start
                previous_port = port
            else:
                port = previous_port+settings.n_cores
                previous_port = port

            simulator_queue[instance_phenotype] = SimulatorQueue(settings.n_cores, settings, port)
            await simulator_queue[instance_phenotype].start()

        analyzer_queue = AnalyzerQueue(1, settings, port+settings.n_cores)
        await analyzer_queue.start()

    population = Population(population_conf, simulator_queue, analyzer_queue, next_robot_id)

    if do_recovery:

        population.load_novelty_archive()

        if gen_num >= 0:
            # loading a previous state of the experiment
            await population.load_snapshot(gen_num)
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

    while gen_num < num_generations-1:
        gen_num += 1
        population = await population.next_gen(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)
        if settings.resimulate != "":
            if str(gen_num+1) in settings.resimulate.split('-'):
                print(f'restart at {gen_num} to renew world')
                sys.exit()

    # output result after completing all generations...
