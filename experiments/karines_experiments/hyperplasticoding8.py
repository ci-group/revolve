#!/usr/bin/env python3
import asyncio

from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.hyperplasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.hyperplasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.hyperplasticoding.initialization import random_initialization
from pyrevolve.genotype.hyperplasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.hyperplasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.hyperplasticoding.hyperplasticoding import HyperPlasticodingConfig
from pyrevolve.tol.manage import measures
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.custom_logging.logger import logger
import sys
import neat
import pprint
import time


async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 200
    population_size = 100
    offspring_size = 100
    front = 'none'

    # environment world and z-start
    environments = {'plane': 0.03
                    }

    #TODO: move it to config!
    # calculation of the measures can be on or off, because they are expensive
    novelty_on = {'novelty': False,
                  'novelty_pop': True
                  }

    cppn_config_path = 'pyrevolve/genotype/hyperplasticoding/config-nonplastic-8'

    genotype_conf = HyperPlasticodingConfig(
        plastic=False,
        cppn_config_path=cppn_config_path
    )

    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=genotype_conf,
        cppn_config_path=cppn_config_path
    )

    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
        cppn_config_path=cppn_config_path
    )
    # experiment params #

    # Parse command line / file input arguments
    settings = parser.parse_args()

    experiment_management = ExperimentManagement(settings, environments)
    neat_experiment_is_new, neat_checkpoint = experiment_management.neat_experiment_is_new()

    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)

    if not neat_experiment_is_new:

        pp = pprint.PrettyPrinter(width=41, compact=True)
        pp.pprint(neat_checkpoint)

        print('members')
        if 'neat' in neat_checkpoint.keys():
            for one_species in neat_checkpoint['neat']['species'].species:
                for member in neat_checkpoint['neat']['species'].species[one_species].members:
                    print('member', neat_checkpoint['neat']['species'].species[one_species].members[member].key,
                          neat_checkpoint['neat']['species'].species[one_species].members[member].fitness)
                    
        gen_num = neat_checkpoint['neat']['latest_snapshot']
        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
        else:
            gen_num += 1
    else:
        gen_num = 0

    def fitness_function_plane(measures, robot):
        return fitness.displacement_velocity_hill(measures, robot)

    fitness_function = {'plane': fitness_function_plane}

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
        novelty_on=novelty_on,
        front=front,
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
                port = previous_port+settings.n_cores
                previous_port = port

            simulator_queue[environment] = SimulatorQueue(settings.n_cores, settings, port)
            await simulator_queue[environment].start()

        analyzer_queue = AnalyzerQueue(1, settings, port+settings.n_cores)
        await analyzer_queue.start()

    population = Population(population_conf, simulator_queue, analyzer_queue)

    if not neat_experiment_is_new:

        population.load_novelty_archive()

        population.neat = neat_checkpoint['neat']
        population.individuals = neat_checkpoint['individuals']

        print('currentttttttt gen',gen_num)
        if gen_num >= 0:
            logger.info('Recovered snapshot '+str(gen_num)+', pop with ' + str(len(population.individuals))+' individuals')

        if gen_num <= 0:
            await population.init_pop_neat()
        else:
            population = await population.next_gen_neat(gen_num)

    else:

        population.neat['reporters'] = neat.reporting.ReporterSet()
        population.neat['config'] = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                                cppn_config_path)
        stagnation = population.neat['config'].stagnation_type(
            population.neat['config'].stagnation_config, population.neat['reporters'])
        population.neat['reproduction'] = population.neat['config'].reproduction_type(
            population.neat['config'].reproduction_config,
            population.neat['reporters'], stagnation)

        # starting a new experiment
        experiment_management.create_exp_folders()
        await population.init_pop_neat()
        
    while gen_num < num_generations-1:
        gen_num += 1
        population = await population.next_gen_neat(gen_num)

    # output result after completing all generations...
