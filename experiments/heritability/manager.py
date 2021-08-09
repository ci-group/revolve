#!/usr/bin/env python3
from __future__ import annotations

import os

from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.direct_tree.direct_tree_crossover import DirectTreeCrossoverConfig, Crossover
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenomeConfig
from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeNEATGenotypeConfig, \
    DirectTreeNEATGenotype
from pyrevolve.genotype.direct_tree.direct_tree_mutation import DirectTreeNEATMutationConfig, DirectTreeMutationConfig, Mutator
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.custom_logging.logger import logger
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenomeConfig


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyrevolve.evolution.individual import Individual


async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 50
    population_size = 100
    offspring_size = 50

    body_conf = DirectTreeGenomeConfig(

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
    genotype_conf = DirectTreeNEATGenotypeConfig(body_conf, brain_conf)

    tree_mutation_conf = DirectTreeMutationConfig(

    )

    genotype_mutation_conf = DirectTreeNEATMutationConfig(
        tree_mutation_conf=tree_mutation_conf,
        neat_conf=brain_conf,
    )

    mutation = Mutator()  # TODO

    crossover_conf = DirectTreeCrossoverConfig(

    )

    crossover = Crossover()  # TODO

    # experiment params #

    # Parse command line / file input arguments
    args = parser.parse_args()
    experiment_management = ExperimentManagement(args)
    has_offspring = False
    do_recovery = args.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info(f'Activated run {args.run} of experiment {args.experiment_name}')

    if do_recovery:
        gen_num, has_offspring, next_robot_id, next_species_id = \
            experiment_management.read_recovery_state(population_size, offspring_size, species=False, n_developments=2)

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

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=DirectTreeNEATGenotype,
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity,
        objective_functions=None,
        mutation_operator=mutation.mutate,
        mutation_conf=genotype_mutation_conf,
        crossover_operator=crossover.crossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=args.evaluation_time,
        grace_time=args.grace_time,
        offspring_size=offspring_size,
        experiment_name=args.experiment_name,
        experiment_management=experiment_management,
    )

    n_cores = args.n_cores

    simulator_queue = SimulatorQueue(n_cores, args, args.port_start)
    await simulator_queue.start()

    analyzer_queue = AnalyzerQueue(1, args, args.port_start+n_cores)
    await analyzer_queue.start()

    population = Population(population_conf, simulator_queue, analyzer_queue, next_robot_id)

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

    while gen_num < num_generations-1:
        gen_num += 1
        population = await population.next_generation(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)
