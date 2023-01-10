#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Optional, AnyStr

import math
import numpy as np
from isaacgym import gymapi

from pyrevolve.genotype.neat_brain_genome.crossover import NEATCrossoverConf
from pyrevolve.evolution.individual import Individual
from pyrevolve.genotype.tree_body_hyperneat_brain.crossover import standard_crossover
from pyrevolve.genotype.tree_body_hyperneat_brain.mutation import standard_mutation
from pyrevolve import parser, SDF
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import generational_population_management, \
    steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype, DirectTreeGenotypeConfig
from pyrevolve.genotype.tree_body_hyperneat_brain import DirectTreeCPGHyperNEATGenotypeConfig, \
    DirectTreeCPGHyperNEATGenotype
from pyrevolve.util.supervisor import CeleryQueue
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenomeConfig, BrainType
from pyrevolve.util.supervisor.rabbits import GazeboCeleryWorkerSupervisor
from pyrevolve.custom_logging.logger import logger
from pyrevolve.util.supervisor.rabbits.celery_queue import CeleryPopulationQueue
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.isaac import manage_isaac_multiple
from pyrevolve.tol.manage.robotmanager import RobotManager

INTERNAL_WORKERS = False

CONFIG_PATH: Optional[AnyStr] = None


def environment_constructor(gym: gymapi.Gym,
                            sim: gymapi.Sim,
                            _env_lower: gymapi.Vec3,
                            _env_upper: gymapi.Vec3,
                            _num_per_row: int,
                            env: gymapi.Env) -> float:
    radius: float = 0.2
    asset_options: gymapi.AssetOptions = gymapi.AssetOptions()
    asset_options.density = 1.0
    asset_options.linear_damping = 0.5
    asset_options.angular_damping = 0.5
    pose = gymapi.Transform()

    assert CONFIG_PATH is not None

    if os.path.exists(CONFIG_PATH):
        with open(os.path.join(CONFIG_PATH, 'env_config.txt'), "r") as file:
            for line in file.readlines():
                var, val = line.rsplit('\n')[0].split(":")
                if var == 'ball_r':
                    radius = float(val)
                elif var == 'density':
                    asset_options.density = float(val)
                # elif var == 'friction':
                #     asset_options.friction = float(val)
                elif var == 'lin_damp':
                    asset_options.linear_damping = float(val)
                elif var == 'ang_damp':
                    asset_options.angular_damping = float(val)
        spacing = 1
        offset = spacing / 2
        pos_arena = [[0, -offset],
                     [-offset, 0],
                     [0, offset],
                     [offset, 0]]
        n_layers = 10
        height = n_layers*radius*3
        wall_options = gymapi.AssetOptions()
        wall_options.fix_base_link = True
        wall_options.flip_visual_attachments = True
        wall_options.armature = 0.0001
        enable_self_collision = False
        gym.begin_aggregate(env, 4, 4, enable_self_collision)
        for ind in range(4):
            pose.p = gymapi.Vec3(pos_arena[ind][0],
                                 pos_arena[ind][1], height / 2)
            pose.r = gymapi.Quat.from_euler_zyx(0.0, 0.0, ind * np.pi / 2)
            wall_asset = gym.create_box(sim, spacing, 0.05, height, wall_options)
            gym.create_actor(env, wall_asset, pose, "arena", 1, 0)
        gym.end_aggregate(env)

        ball_spacing = 2 * radius
        min_coord = radius + 0.025
        pose = gymapi.Transform()
        pose.r = gymapi.Quat(0, 0, 0, 1)

        x_max, y_max = (spacing / 2 - min_coord, spacing / 2 - min_coord)
        xmap, ymap = np.meshgrid(np.arange(-x_max, x_max, ball_spacing),
                                 np.arange(-y_max, y_max, ball_spacing))
        xmap = xmap.flatten()
        ymap = ymap.flatten()

        print(f"Spawning {n_layers * xmap.size} balls")
        # gym.begin_aggregate(env, xmap.size * n_layers, xmap.size * n_layers, False)
        for z in range(n_layers):
            offset = (z % 2) * radius
            for x, y in zip(xmap, ymap):
                pose.p = gymapi.Vec3(x + offset, y + offset, min_coord + z * ball_spacing)
                ball_asset = gym.create_sphere(sim, radius, asset_options)
                gym.create_actor(env, ball_asset, pose, None, 1, 0)
        env_height = ball_spacing * n_layers
        # gym.end_aggregate(env)
        print(f"Loaded {n_layers * xmap.size} balls")
        return env_height
    else:
        raise ValueError(f"Could not find {CONFIG_PATH}")


async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 100
    population_size = 100
    offspring_size = 50

    manage_isaac_multiple.ISOLATED_ENVIRONMENTS = True

    morph_single_mutation_prob = 0.2
    morph_no_single_mutation_prob = 1 - morph_single_mutation_prob  # 0.8
    morph_no_all_mutation_prob = morph_no_single_mutation_prob ** 4  # 0.4096
    morph_at_least_one_mutation_prob = 1 - morph_no_all_mutation_prob  # 0.5904

    brain_single_mutation_prob = 0.5

    tree_genotype_conf: DirectTreeGenotypeConfig = DirectTreeGenotypeConfig(
        max_parts=20,
        min_parts=5,
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

    neat_conf: NeatBrainGenomeConfig = NeatBrainGenomeConfig(
        brain_type=BrainType.CPG,
        random_seed=None,
        apply_mutation_constraints=False,
    )

    neat_crossover_conf: NEATCrossoverConf = NEATCrossoverConf(
        apply_constraints=False,
    )

    genotype_conf: DirectTreeCPGHyperNEATGenotypeConfig = DirectTreeCPGHyperNEATGenotypeConfig(
        direct_tree_conf=tree_genotype_conf,
        neat_conf=neat_conf,
        neat_crossover_conf=neat_crossover_conf,
        number_of_brains=1,
    )

    def genotype_test_fun(candidate_genotype: DirectTreeCPGHyperNEATGenotype) -> bool:
        # TODO test if the robot is bigger than the pool!
        for brain_gen in candidate_genotype._brain_genomes:
            if brain_gen._neat_genome.FailsConstraints(neat_conf.multineat_params):
                return False
        return True


    # Parse command line / file input arguments
    args = parser.parse_args()
    experiment_management = ExperimentManagement(args)
    has_offspring = False
    do_recovery = args.recovery_enabled and not experiment_management.experiment_is_new()

    global CONFIG_PATH
    CONFIG_PATH = os.path.join(experiment_management._experiment_folder, '..', f'logs_{args.run}')

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

    def fitness_fun(robot_manager: RobotManager, robot: RevolveBot) -> float:
        # TODO test for the z-height of the lowest point
        # integrate the "z-height of the lowest point" in time.
        # (need to change the simulator manager part, it needs to report the position of the lowest block, not the center)

        lowest_pos_integrate = 0.0
        for pos, t in zip(robot_manager._positions, robot_manager._times):
            dt = 1.0  # TODO maybe calculate this?
            lowest_pos_integrate += pos*dt

        # we want to maximize this value
        return lowest_pos_integrate

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=lambda conf, _id: DirectTreeCPGHyperNEATGenotype(conf, _id, random_init_body=True),
        genotype_conf=genotype_conf,
        fitness_function=fitness_fun,
        objective_functions=None,
        mutation_operator=lambda genotype, gen_conf: standard_mutation(genotype, gen_conf),
        mutation_conf=genotype_conf,
        crossover_operator=lambda parents, gen_conf, _: standard_crossover(parents, gen_conf),
        crossover_conf=None,
        genotype_test=genotype_test_fun,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,  # must be none for generational management function
        evaluation_time=args.evaluation_time,
        grace_time=args.grace_time,
        offspring_size=offspring_size,
        experiment_name=args.experiment_name,
        experiment_management=experiment_management,
        environment_constructor=environment_constructor,
        population_batch_size=1,
    )

    n_cores = args.n_cores

    def worker_crash(process, exit_code) -> None:
        logger.fatal(f'GazeboCeleryWorker died with code: {exit_code} ({process})')

    # CELERY CONNECTION (includes database connection)
    # simulator_queue = CeleryQueue(args, args.port_start, dbname='revolve', db_addr='127.0.0.1', use_isaacgym=True)
    simulator_queue = CeleryPopulationQueue(args, use_isaacgym=True, local_computing=True)
    await simulator_queue.start(cleanup_database=True)

    # CELERY GAZEBO WORKER
    celery_workers: List[GazeboCeleryWorkerSupervisor] = []
    if INTERNAL_WORKERS:
        for n in range(n_cores):
            celery_worker = GazeboCeleryWorkerSupervisor(
                world_file='worlds/plane.celery.world',
                gui=args.gui,
                simulator_args=['--verbose'],
                plugins_dir_path=os.path.join('../heritability', 'build', 'lib'),
                models_dir_path=os.path.join('../heritability', 'models'),
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
