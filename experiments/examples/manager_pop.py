#!/usr/bin/env python3
import asyncio

from pyrevolve import parser
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution import fitness
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import (
    steady_state_population_management,
)
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeGenotypeConfig
from pyrevolve.genotype.direct_tree.direct_tree_crossover import (
    crossover_list as direct_tree_crossover_list,
)
from pyrevolve.genotype.direct_tree.direct_tree_genotype import (
    Genotype as DirectTreeGenotype,
)
from pyrevolve.genotype.direct_tree.direct_tree_mutation import (
    mutate as direct_tree_mutate,
)
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue


async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 100
    population_size = 100
    offspring_size = 50

    genotype_conf: DirectTreeGenotypeConfig = DirectTreeGenotypeConfig(
        max_parts=50,
        min_parts=10,
        max_oscillation=5,
        init_n_parts_mu=10,
        init_n_parts_sigma=4,
        init_prob_no_child=0.1,
        init_prob_child_block=0.4,
        init_prob_child_active_joint=0.5,
        mutation_p_duplicate_subtree=0.2,
        mutation_p_delete_subtree=0.2,
        mutation_p_generate_subtree=0.2,
        mutation_p_swap_subtree=0.2,
        mutation_p_mutate_oscillators=0.5,
        mutation_p_mutate_oscillator=0.5,
        mutate_oscillator_amplitude_sigma=0.3,
        mutate_oscillator_period_sigma=0.3,
        mutate_oscillator_phase_sigma=0.3,
    )
    mutation_conf = genotype_conf
    crossover_conf = genotype_conf

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)
    do_recovery = (
        settings.recovery_enabled and not experiment_management.experiment_is_new()
    )

    logger.info(
        "Activated run " + settings.run + " of experiment " + settings.experiment_name
    )

    if do_recovery:
        (
            gen_num,
            has_offspring,
            next_robot_id,
            _,
        ) = experiment_management.read_recovery_state(population_size, offspring_size)

        if gen_num == num_generations - 1:
            logger.info("Experiment is already complete.")
            return
    else:
        gen_num = 0
        next_robot_id = 1

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=lambda conf, _id: DirectTreeGenotype(
            conf, _id, random_init=True
        ),
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity,
        mutation_operator=lambda genotype, gen_conf: direct_tree_mutate(
            genotype, gen_conf, in_place=False
        ),
        mutation_conf=mutation_conf,
        crossover_operator=lambda parents, gen_conf, _cross_conf: direct_tree_crossover_list(
            [p.genotype for p in parents], gen_conf
        ),
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(
            individuals, 2, tournament_selection
        ),
        population_management=steady_state_population_management,
        population_management_selector=None,
        evaluation_time=settings.evaluation_time,
        grace_time=settings.grace_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
    )

    n_cores = settings.n_cores

    settings = parser.parse_args()
    simulator_queue = SimulatorQueue(n_cores, settings, settings.port_start)
    await simulator_queue.start()

    analyzer_queue = AnalyzerQueue(1, settings, settings.port_start + n_cores)
    await analyzer_queue.start()

    population = Population(
        population_conf, simulator_queue, analyzer_queue, next_robot_id
    )

    if do_recovery:
        # loading a previous state of the experiment
        population.load_snapshot(gen_num)
        if gen_num >= 0:
            logger.info(
                "Recovered snapshot "
                + str(gen_num)
                + ", pop with "
                + str(len(population.individuals))
                + " individuals"
            )
        if has_offspring:
            individuals = population.load_offspring(
                gen_num, population_size, offspring_size, next_robot_id
            )
            gen_num += 1
            logger.info("Recovered unfinished offspring " + str(gen_num))

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

    while gen_num < num_generations - 1:
        gen_num += 1
        population = await population.next_generation(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)

    # output result after completing all generations...
