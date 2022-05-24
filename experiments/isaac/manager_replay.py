#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Dict
import yaml

import math
from isaacgym import gymapi

from experiments.isaac.positioned_population import PositionedPopulation
from pyrevolve import parser
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution import fitness
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import generational_population_management
from pyrevolve.evolution.selection import best_selection
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotypeConfig
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenomeConfig, BrainType
from pyrevolve.genotype.tree_body_hyperneat_brain import DirectTreeCPGHyperNEATGenotypeConfig, \
    DirectTreeCPGHyperNEATGenotype
from pyrevolve.genotype.tree_body_hyperneat_brain.crossover import standard_crossover
from pyrevolve.genotype.tree_body_hyperneat_brain.mutation import standard_mutation
from pyrevolve.util.supervisor.rabbits import GazeboCeleryWorkerSupervisor, PostgreSQLDatabase, RobotEvaluation, \
    RobotState
from pyrevolve.util.supervisor.rabbits.celery_queue import CeleryPopulationQueue

INTERNAL_WORKERS = False


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
    sphere_asset = gym.create_sphere(sim, radius, asset_options)
    return 0



# MATING_RANGE = 0.45
MATING_RANGE = 45

async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 200
    population_size = 32
    offspring_size = population_size

    morph_single_mutation_prob = 0.2
    morph_no_single_mutation_prob = 1 - morph_single_mutation_prob  # 0.8
    morph_no_all_mutation_prob = morph_no_single_mutation_prob ** 4  # 0.4096
    morph_at_least_one_mutation_prob = 1 - morph_no_all_mutation_prob  # 0.5904

    brain_single_mutation_prob = 0.5

    tree_genotype_conf: DirectTreeGenotypeConfig = DirectTreeGenotypeConfig(
        max_parts=25,
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
        mutation_p_mutate_oscillator=0,
        mutate_oscillator_amplitude_sigma=0.3,
        mutate_oscillator_period_sigma=0.3,
        mutate_oscillator_phase_sigma=0.3,
    )

    neat_conf: NeatBrainGenomeConfig = NeatBrainGenomeConfig(
        brain_type=BrainType.CPG,
        random_seed=None
    )

    genotype_conf: DirectTreeCPGHyperNEATGenotypeConfig = DirectTreeCPGHyperNEATGenotypeConfig(
        direct_tree_conf=tree_genotype_conf,
        neat_conf=neat_conf,
        number_of_brains=1,
    )

    # Parse command line / file input arguments
    args = parser.parse_args()
    experiment_management = ExperimentManagement(args)
    has_offspring = False
    do_recovery = args.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info(f'Activated run {args.run} of experiment {args.experiment_name}')

    #gen_num, has_offspring, next_robot_id, next_species_id = \
    #    experiment_management.read_recovery_state(population_size, offspring_size, species=False)
    gen_num = args.generation
    if gen_num < 0:
        logger.info('Experiment continuing from first generation')
        gen_num = 1

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=lambda conf, _id: DirectTreeCPGHyperNEATGenotype(conf, _id, random_init_body=True),
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity,
        objective_functions=None,
        mutation_operator=lambda genotype, gen_conf: standard_mutation(genotype, gen_conf),
        mutation_conf=genotype_conf,
        crossover_operator=lambda parents, gen_conf, _: standard_crossover(parents, gen_conf),
        crossover_conf=None,
        selection=best_selection,
        parent_selection=None,
        population_management=generational_population_management,
        population_management_selector=None,
        evaluation_time=args.evaluation_time,
        grace_time=args.grace_time,
        offspring_size=offspring_size,
        experiment_name=args.experiment_name,
        experiment_management=experiment_management,
        environment_constructor=environment_constructor, #TODO IMPLEMENT THIS!!!! pass it to isaacqueue that passes it to the manage_isaac_multiple
    )

    n_cores = args.n_cores

    def worker_crash(process, exit_code) -> None:
        logger.fatal(f'GazeboCeleryWorker died with code: {exit_code} ({process})')

    # CELERY CONNECTION (includes database connection)
    # simulator_queue = CeleryQueue(args, args.port_start, dbname='revolve', db_addr='127.0.0.1', use_isaacgym=True)
    simulator_queue = CeleryPopulationQueue(args, use_isaacgym=True, local_computing=True)
    await simulator_queue.start(cleanup_database=False)

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
    population = PositionedPopulation(population_conf, simulator_queue, analyzer_queue)

    # loading a previous state of the experiment
    population.load_snapshot(gen_num, multi_development=True)
    load_database_ids(gen_num, experiment_management,population.individuals)
    if gen_num >= 0:
        logger.info(f'Recovered snapshot {gen_num}, pop with {len(population.individuals)} individuals')

    #new_population = await population.next_generation(gen_num)
    update_robot_pose(population.individuals, simulator_queue._db)
    await population.evaluate(population.individuals, gen_num)

    # CLEANUP
    for celery_worker in celery_workers:
        await celery_worker.stop()
    await simulator_queue.stop()

def update_robot_pose(individuals: List[Individual], db: PostgreSQLDatabase) -> None:
    
    with db.session() as session:

        last_eval: RobotEvaluation = session \
            .query(RobotEvaluation) \
            .filter(RobotEvaluation.robot_id == individuals[0].id) \
            .order_by(RobotEvaluation.n.desc()) \
            .one()
        last_eval_n = last_eval.n
        assert last_eval_n == 0

        for individual in individuals:
            dbid = int(individual.phenotype.database_id)
            final_position = session \
                .query(RobotState.pos_x, RobotState.pos_y) \
                .filter(RobotState.evaluation_n == last_eval_n) \
                .filter(RobotState.evaluation_robot_id == dbid) \
                .order_by(RobotState.time_sec.desc(), RobotState.time_nsec.desc()) \
                .first()
            print(f"DB:{individual} ({final_position})")
            individual.pose.x = final_position[0]
            individual.pose.y = final_position[1]

def load_database_ids(gen_num: int, experiment_management: ExperimentManagement, individuals: List[Individual]):
    database_ids = {}
    with open(f'{experiment_management.generation_folder(gen_num-1)}/database_ids.yml', 'r') as database_id_file:
        database_ids = yaml.safe_load(database_id_file)
    for ind in individuals:
        ind.phenotype.database_id = database_ids[ind.phenotype.id]