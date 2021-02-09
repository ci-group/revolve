#!/usr/bin/env python3
from __future__ import annotations

import os
import asyncio

from pyrevolve import parser
from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.direct_tree.direct_tree_crossover import DirectTreeCrossoverConfig, Crossover
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenomeConfig, DirectTreeGenotype
from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeNEATGenotypeConfig, \
    DirectTreeNEATGenotype
from pyrevolve.genotype.direct_tree.tree_mutation import DirectTreeNEATMutationConfig, DirectTreeMutationConfig, Mutator
from pyrevolve.tol.spec import get_tree_generator
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.custom_logging.logger import logger
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenomeConfig
from pyrevolve.genotype.direct_tree import DirectTreeConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyrevolve.evolution.individual import Individual


def tree_random_initialization(conf: DirectTreeConfig, _id: int) -> DirectTreeGenotype:
    genotype: DirectTreeGenotype = DirectTreeGenotype(conf, _id)
    genotype.generator = get_tree_generator(conf)
    genotype.representation = genotype.generator.generate_tree()
    return genotype


async def run():
    # experiment params #
    num_generations = 10
    population_size = 10
    offspring_size = 5

    genotype_config = DirectTreeConfig(min_parts=5, max_parts=11, max_inputs=3, max_outputs=6,
                                       initial_parts_mu=8, initial_parts_sigma=1.5,
                                       disable_sensors=True, enable_touch_sensor=False)

    crossover_config = DirectTreeCrossoverConfig()
    mutation_config = DirectTreeMutationConfig()

    robogen_tree_generator: RobogenTreeGenerator = get_tree_generator(genotype_config)
    mutation: Mutator       = Mutator(robogen_tree_generator)
    crossover: Crossover    = Crossover(robogen_tree_generator)

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
        genotype_constructor=tree_random_initialization,
        genotype_conf=genotype_config,
        fitness_function=fitness.displacement_velocity,
        objective_functions=None,
        mutation_operator=mutation.mutate,
        mutation_conf=mutation_config,
        crossover_operator=crossover.crossover,
        crossover_conf=crossover_config,
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

    population = Population(population_conf, None, None, next_robot_id)
    """
    if do_recovery:
        # loading a previous state of the experiment
        print(experiment_management._generations_folder)
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
    """
    # starting a new experiment
    experiment_management.create_exp_folders()
    await population.initialize()
    experiment_management.export_snapshots(population.individuals, gen_num)

    while gen_num < num_generations-1:
        gen_num += 1
        population = await population.next_generation(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
    loop.close()
