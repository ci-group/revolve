#!/usr/bin/env python3
from __future__ import annotations

from pyrevolve import parser

from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import steady_state_population_management

from pyrevolve.experiment_management import ExperimentManagement

from pyrevolve.genotype.lsystem_neat.crossover import CrossoverConfig as lCrossoverConfig
from pyrevolve.genotype.lsystem_neat.crossover import standard_crossover as lcrossover
from pyrevolve.genotype.lsystem_neat.mutation import LSystemNeatMutationConf as lMutationConfig
from pyrevolve.genotype.lsystem_neat.mutation import standard_mutation as lmutation
from pyrevolve.genotype.lsystem_neat.lsystem_neat_genotype import LSystemCPGHyperNEATGenotype, LSystemCPGHyperNEATGenotypeConfig
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig as plasticMutationConfig

from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue

from pyrevolve.custom_logging.logger import logger

from pyrevolve.genotype.plasticoding import PlasticodingConfig
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenomeConfig


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyrevolve.evolution.individual import Individual


async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 3
    population_size = 3
    offspring_size = 2

    body_conf = PlasticodingConfig(
        max_structural_modules=50,
        allow_vertical_brick=True,
        use_movement_commands=True,
        use_rotation_commands=False,
        use_movement_stack=False,
        allow_joint_joint_attachment=False,
    )
    brain_conf = NeatBrainGenomeConfig()
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

    plasticMutation_conf = plasticMutationConfig(
        mutation_prob=0.8,
        genotype_conf=body_conf
    )

    lmutation_conf = lMutationConfig(
        plasticoding_mutation_conf=plasticMutation_conf,
        neat_conf=brain_conf,
    )

    crossover_conf = lCrossoverConfig(
        crossover_prob=0.8,
    )

    # experiment params #

    # Parse command line / file input arguments
    args = parser.parse_args()
    experiment_management = ExperimentManagement(args)
    has_offspring = False
    do_recovery = args.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info(f'Activated run {args.run} of experiment {args.experiment_name}')

    if do_recovery:
        gen_num, has_offspring, next_robot_id, next_species_id = \
            experiment_management.read_recovery_state(population_size, offspring_size, species=False)

        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0
        next_robot_id = 1

    if gen_num < 0:
        logger.info('Experiment continuing from first generation')
        gen_num = 0

    if next_robot_id < 0:
        next_robot_id = 1

    # Experimental selection of fitness function from config fitness argument.
    fitness_function = getattr(fitness, args.fitness)

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=LSystemCPGHyperNEATGenotype,
        genotype_conf=genotype_conf,
        fitness_function=fitness_function,
        mutation_operator=lmutation,
        mutation_conf=lmutation_conf,
        crossover_operator=lcrossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=args.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=args.experiment_name,
        experiment_management=experiment_management,
    )

    n_cores = args.n_cores

    simulator_queue = SimulatorQueue(n_cores, args, args.port_start)
    await simulator_queue.start()

    analyzer_queue = AnalyzerQueue(1, args, args.port_start+n_cores)
    await analyzer_queue.start()

    population = Population(population_conf,
                                     simulator_queue,
                                     analyzer_queue,
                                     next_robot_id)

    if do_recovery:
        # loading a previous state of the experiment
        population.load_snapshot(gen_num)
        if gen_num >= 0:
            logger.info('Recovered snapshot '+str(gen_num)+', pop with ' + str(len(population.individuals))+' individuals')
        if has_offspring:
            individuals = population.load_offspring(gen_num, population_size, offspring_size, next_robot_id)
            gen_num += 1
            logger.info('Recovered unfinished offspring '+str(gen_num))

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

    while gen_num < num_generations-1:
        gen_num += 1
        population = await population.next_generation(gen_num)
        logger.info("after next generation\n")
        experiment_management.export_snapshots(population.individuals, gen_num)
