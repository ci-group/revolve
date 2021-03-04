#!/usr/bin/env python3
import sys

from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population import PopulationConfig, DummyPopulation
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.lsystem_cpg.cpg_brain import CPGBrainGenomeConfig
from pyrevolve.genotype.lsystem_cpg.crossover import CrossoverConfig
from pyrevolve.genotype.lsystem_cpg.crossover import standard_crossover
from pyrevolve.genotype.lsystem_cpg.lsystem_cpg_genotype import LSystemCPGGenotypeConfig, LSystemCPGGenotype
from pyrevolve.genotype.plasticoding import PlasticodingConfig
from pyrevolve.genotype.lsystem_cpg.mutation import standard_mutation
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.custom_logging.logger import logger

import logging
from pyrevolve import parser
from pyrevolve.custom_logging import logger


async def run():
    """
    The main coroutine, which is started below.
    """
    log = logger.create_logger('experiment', handlers=[
        logging.StreamHandler(sys.stdout),
    ])

    # Set debug level to DEBUG
    log.setLevel(logging.DEBUG)

    # experiment params #
    num_generations = 10
    population_size = 10
    offspring_size = 5

    plasticoding_config = PlasticodingConfig(
        max_structural_modules=20,
        allow_vertical_brick=True,
        use_movement_commands=True,
        use_rotation_commands=False,
        use_movement_stack=True
    )

    cpg_config = CPGBrainGenomeConfig()

    lsystem_cpg_config = LSystemCPGGenotypeConfig(plasticoding_config, cpg_config)

    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=plasticoding_config,
    )

    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
    )
    # experiment params #

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    log.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)

    if do_recovery:
        gen_num, has_offspring, next_robot_id = experiment_management.read_recovery_state(population_size, offspring_size)

        if gen_num == num_generations-1:
            log.info('Experiment is already complete.')
            return
    else:
        gen_num = 0
        next_robot_id = 1

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=LSystemCPGGenotype,
        genotype_conf=lsystem_cpg_config,
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

    population = DummyPopulation(population_conf, next_robot_id)

    # starting a new experiment
    experiment_management.create_exp_folders()
    population.init_pop()

    while gen_num < num_generations-1:
        gen_num += 1
        population = population.next_gen(gen_num)

    # output result after completing all generations...
