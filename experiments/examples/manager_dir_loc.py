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
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.neat_brain_genome import NeatBrainGenomeConfig
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import BrainType
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding import PlasticodingConfig
from pyrevolve.genotype.lsystem_neat.crossover import CrossoverConfig as lCrossoverConfig
from pyrevolve.genotype.lsystem_neat.crossover import standard_crossover as lcrossover
from pyrevolve.genotype.lsystem_neat.mutation import LSystemNeatMutationConf as lMutationConfig
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig as plasticMutationConfig
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.genotype.lsystem_neat import LSystemCPGHyperNEATGenotypeConfig, LSystemCPGHyperNEATGenotype
from pyrevolve.genotype.lsystem_neat.mutation import standard_mutation as lmutation


async def run():
    #################################### SETTING UP THE EXPERIMENT #####################################
    # Define experiment paramameters
    num_generations = 100
    population_size = 100
    offspring_size = 50

    # Using L-system encoding
    body_conf: PlasticodingConfig = PlasticodingConfig(
        allow_joint_joint_attachment=False,
        e_max_groups=3,
        oscillator_param_min=0,
        oscillator_param_max=5,
        weight_param_min=0,
        weight_param_max=0,
        weight_min=0,
        weight_max=0,
        max_structural_modules=50,
        allow_vertical_brick=True,
        use_movement_commands=True,
        use_rotation_commands=False,
        use_movement_stack=False,
    )
    brain_conf = NeatBrainGenomeConfig(brain_type=BrainType.CPG)
    brain_conf.multineat_params.DisjointCoeff = 0.3
    brain_conf.multineat_params.ExcessCoeff = 0.3
    brain_conf.multineat_params.WeightDiffCoeff = 0.3
    brain_conf.multineat_params.ActivationADiffCoeff = 0.3
    brain_conf.multineat_params.ActivationBDiffCoeff = 0.3
    brain_conf.multineat_params.TimeConstantDiffCoeff = 0.3
    brain_conf.multineat_params.BiasDiffCoeff = 0.3
    brain_conf.multineat_params.ActivationFunctionDiffCoeff = 0.3
    brain_conf.multineat_params.CompatTreshold = 3.0
    brain_conf.multineat_params.MinCompatTreshold = 3.0
    brain_conf.multineat_params.CompatTresholdModifier = 0.1
    brain_conf.multineat_params.CompatTreshChangeInterval_Generations = 1
    brain_conf.multineat_params.CompatTreshChangeInterval_Evaluations = 1
    genotype_conf = LSystemCPGHyperNEATGenotypeConfig(body_conf, brain_conf)

    # prob of mutation for new individual
    plasticMutation_conf: MutationConfig = plasticMutationConfig(
        mutation_prob=0.6,
        genotype_conf=body_conf,
    )

    # Define the mutation probability
    lmutation_conf = lMutationConfig(
        plasticoding_mutation_conf=plasticMutation_conf,
        neat_conf=brain_conf,
    )

    crossover_conf = lCrossoverConfig(
        crossover_prob=1.0,
    )

    # # Define fitness evaluation
    # fitness_function = fitness.directed_locomotion(
    #     target_direction=0.0,
    # )

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    # Print experiment information
    logger.info('Activated run ' + settings.run + ' of experiment ' + settings.experiment_name)

    # Loading the generation count of a previous experiment (after a crash),
    #   or initialize the generation count for a new experiment
    if do_recovery:
        gen_num, has_offspring, next_robot_id, next_species_id = \
            experiment_management.read_recovery_state(population_size, offspring_size, species=False)

        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0
        next_robot_id = 1

    # Insert the population parameters PopulationConfig:
    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=lambda conf, _id: LSystemCPGHyperNEATGenotype(conf, _id),
        genotype_conf=genotype_conf,
        fitness_function=fitness.directed_locomotion,
        # fitness_function=lambda manager, robot: fitness.directed_locomotion(robot, target_direction=0.0, weight=0.01),
        mutation_operator=lambda genotype, gen_conf: lmutation(genotype, gen_conf),
        mutation_conf=lmutation_conf,
        crossover_operator=lambda parents, gen_conf, cross_conf: lcrossover(parents, gen_conf, cross_conf),
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
    population: Population = Population(population_conf, simulator_queue, analyzer_queue, next_robot_id)

    # Create the next generation based on a current population by:
    #   Loading the last generation/offspring of a previous experiment (after a crash),
    #   or initializing a first generation for a new experiment
    if do_recovery:
        # loading a previous state of the experiment
        population.load_snapshot(gen_num, multi_development=True)
        if gen_num >= 0:
            logger.info(f'Recovered snapshot {gen_num}, pop with {len(population.individuals)} individuals')
        if has_offspring:
            individuals = population.load_offspring(gen_num, population_size, offspring_size, next_robot_id)
            gen_num += 1
            logger.info(f'Recovered unfinished offspring {gen_num}')

            if gen_num == 0:
                await population.initialize(individuals)
            else:
                population = await population.next_generation(gen_num, individuals)

            experiment_management.export_snapshots(population.individuals, gen_num)
    else:
        # starting a new experiment
        experiment_management.create_exp_folders()
        await population.initialize()
        experiment_management.export_snapshots(population.individuals, gen_num)

    ################################## RUN THE REST OF THE EXPERIMENT ##################################
    # Start the while loop that produces new generations based on previous one
    while gen_num < num_generations - 1:
        gen_num += 1
        population = await population.next_generation(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)

    # output result after completing all generations...
    # experiment_folder = .../revolve/data/<experiment_name>/<run>