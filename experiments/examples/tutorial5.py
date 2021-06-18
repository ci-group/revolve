"""
Online evolution experiment. This experiment is just a test script:
- Using default settings
- Evolving 10 generations
- With a population size of 20 robots
- Constructing 10 new robots after every gen.
"""
# !/usr/bin/env python3
import asyncio

from pyrevolve import parser
from pyrevolve.custom_logging.logger import logger
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
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue


async def run():
    #################################### SETTING UP THE EXPERIMENT #####################################
    # Define experiment paramameters
    num_generations = 10
    population_size = 20
    offspring_size = 10

    # Define the maximum number of structural modules per robot
    genotype_conf = PlasticodingConfig(
        max_structural_modules=100,
    )
    # Define the mutation probability
    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=genotype_conf,
    )
    # Define the Crossover probability
    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
    )

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    # Print experiment information
    logger.info('Activated run ' + settings.run + ' of experiment ' + settings.experiment_name)

    # Loading the generation count of a previous experiment (after a crash),
    #   or initialize the generation count for a new experiment
    if do_recovery:
        gen_num, has_offspring, next_robot_id = experiment_management.read_recovery_state(population_size,
                                                                                          offspring_size)

        if gen_num == num_generations - 1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0
        next_robot_id = 1

    # Insert the population parameters PopulationConfig:
    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity,
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
    )

    # Define the number of simultaneous simulations [default =1]
    n_cores = settings.n_cores

    ############################### SETTING UP THE FIRST NEW GENERATION ###############################
    # Start the connection to the gazebo simulator with the proper DynamicSupervisor() settings in SimulatorQueue
    settings = parser.parse_args()
    simulator_queue = SimulatorQueue(n_cores, settings, settings.port_start)
    await simulator_queue.start()

    # Start the connection of the evaluation script RobotAnalyzer() to the simulator in AnalyzerQueue
    analyzer_queue = AnalyzerQueue(1, settings, settings.port_start + n_cores)
    await analyzer_queue.start()

    # Create a Population object that initialises:
    #   individuals in the population with an empty list,
    #   and stores the configuration of the system to the conf variable.
    population = Population(population_conf, simulator_queue, analyzer_queue, next_robot_id)

    # Create the next generation based on a current population by:
    #   Loading the last generation/offspring of a previous experiment (after a crash),
    #   or initializing a first generation for a new experiment
    if do_recovery:
        # loading a previous state of the experiment
        await population.load_snapshot(gen_num)
        if gen_num >= 0:
            logger.info('Recovered snapshot ' + str(gen_num) + ', pop with ' + str(
                len(population.individuals)) + ' individuals')
        if has_offspring:
            individuals = await population.load_offspring(gen_num, population_size, offspring_size, next_robot_id)
            gen_num += 1
            logger.info('Recovered unfinished offspring ' + str(gen_num))

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

    ################################## RUN THE REST OF THE EXPERIMENT ##################################
    # Start the while loop that produces new generations based on previous one
    while gen_num < num_generations - 1:
        gen_num += 1
        population = await population.next_gen(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)

    # output result after completing all generations...
    # experiment_folder = .../revolve/data/<experiment_name>/<run>