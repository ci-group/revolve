#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List

from pyrevolve.genotype.direct_tree.direct_tree_crossover import crossover_list
from pyrevolve.genotype.direct_tree.direct_tree_mutation import mutate
from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import generational_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype, DirectTreeGenotypeConfig
from pyrevolve.util.supervisor import CeleryQueue
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.rabbits import GazeboCeleryWorkerSupervisor
from pyrevolve.custom_logging.logger import logger

INTERNAL_WORKERS = False


async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 50
    population_size = 100
    offspring_size = 100

    morph_single_mutation_prob = 0.2
    morph_no_single_mutation_prob = 1 - morph_single_mutation_prob  # 0.8
    morph_no_all_mutation_prob = morph_no_single_mutation_prob ** 4  # 0.4096
    morph_at_least_one_mutation_prob = 1 - morph_no_all_mutation_prob  # 0.5904

    brain_single_mutation_prob = 0.5

    genotype_conf: DirectTreeGenotypeConfig = DirectTreeGenotypeConfig(
        max_parts=50,
        min_parts=10,
        max_oscillation=5,
        init_n_parts_mu=10,
        init_n_parts_sigma=4,
        init_prob_no_child=0.1,
        init_prob_child_block=0.4,
        init_prob_child_active_joint=0.5,
        mutation_p_duplicate_subtree=morph_single_mutation_prob,
        mutation_p_delete_subtree=morph_single_mutation_prob,
        mutation_p_generate_subtree=morph_single_mutation_prob,
        mutation_p_swap_subtree=morph_single_mutation_prob,
        mutation_p_mutate_oscillators=brain_single_mutation_prob,
        mutation_p_mutate_oscillator=0.5,
        mutate_oscillator_amplitude_sigma=0.3,
        mutate_oscillator_period_sigma=0.3,
        mutate_oscillator_phase_sigma=0.3,
    )

    # Parse command line / file input arguments
    args = parser.parse_args()
    experiment_management = ExperimentManagement(args)
    has_offspring = False
    do_recovery = args.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info(f'Activated run {args.run} of experiment {args.experiment_name}')

    if do_recovery:
        gen_num, has_offspring, next_robot_id, next_species_id = \
            experiment_management.read_recovery_state(population_size, offspring_size, species=False)

        if gen_num == num_generations - 1:
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
        genotype_constructor=lambda conf, _id: DirectTreeGenotype(conf, _id, random_init=True),
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity,
        objective_functions=None,
        mutation_operator=lambda genotype, gen_conf: mutate(genotype, gen_conf, in_place=False),
        mutation_conf=genotype_conf,
        crossover_operator=lambda parents, gen_conf, _cross_conf: crossover_list([p.genotype for p in parents], gen_conf),
        crossover_conf=genotype_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=generational_population_management,
        population_management_selector=None,  # must be none for generational management function
        evaluation_time=args.evaluation_time,
        grace_time=args.grace_time,
        offspring_size=offspring_size,
        experiment_name=args.experiment_name,
        experiment_management=experiment_management,
    )

    n_cores = args.n_cores

    def worker_crash(process, exit_code) -> None:
        logger.fatal(f'GazeboCeleryWorker died with code: {exit_code} ({process})')

    # CELERY CONNECTION (includes database connection)
    simulator_queue = CeleryQueue(args, args.port_start, dbname='revolve')
    await simulator_queue.start(cleanup_database=True)

    # CELERY GAZEBO WORKER
    celery_workers: List[GazeboCeleryWorkerSupervisor] = []
    if INTERNAL_WORKERS:
        for n in range(n_cores):
            celery_worker = GazeboCeleryWorkerSupervisor(
                world_file='worlds/plane.celery.world',
                gui=args.gui,
                simulator_args=['--verbose'],
                plugins_dir_path=os.path.join('.', 'build', 'lib'),
                models_dir_path=os.path.join('.', 'models'),
                simulator_name=f'GazeboCeleryWorker_{n}',
                process_terminated_callback=worker_crash,
            )
            await celery_worker.launch_simulator(port=args.port_start + n)
            celery_workers.append(celery_worker)

    # ANALYZER CONNECTION
    # analyzer_port = args.port_start + (n_cores if INTERNAL_WORKERS else 0)
    # analyzer_queue = AnalyzerQueue(1, args, port_start=analyzer_port)
    # await analyzer_queue.start()
    analyzer_queue = None

    # INITIAL POPULATION OBJECT
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

    while gen_num < num_generations - 1:
        gen_num += 1
        population = await population.next_generation(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)

    # CLEANUP
    for celery_worker in celery_workers:
        await celery_worker.stop()
    await simulator_queue.stop()
