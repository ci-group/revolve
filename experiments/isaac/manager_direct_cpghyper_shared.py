#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import List, Dict

import numpy as np
import yaml
import wandb

import math
from isaacgym import gymapi

from experiments.isaac.positioned_population import PositionedPopulation
from pyrevolve.genotype.neat_brain_genome.crossover import NEATCrossoverConf
from pyrevolve import parser
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution import fitness
from pyrevolve.tol.manage import measures
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
    RobotState, Robot as DBRobot
from pyrevolve.util.supervisor.rabbits.celery_queue import CeleryPopulationQueue
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.tol.manage.robotmanager import RobotManager
from pyrevolve.isaac import manage_isaac_multiple

INTERNAL_WORKERS = False
PROGENITOR = False
FITNESS = 'displacement_velocity'
START_FROM_PREVIOUS_POPULATION = True


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


def generate_candidate_partners(population: PositionedPopulation, db: PostgreSQLDatabase, grace_time: float = 0.) -> None:
    ids: List[int] = [int(individual.phenotype.database_id) for individual in population.individuals]
    individual_map: Dict[int, Individual] = {int(individual.phenotype.database_id): individual for individual in population.individuals }

    # Using a set for candidates to avoid repetitions
    # TODO if a robot is seen more, should it get more chances?
    for individual in population.individuals:
        individual.candidate_partners = set()

    with db.session() as session:
        last_eval: RobotEvaluation = session \
            .query(RobotEvaluation) \
            .filter(RobotEvaluation.robot_id == ids[0]) \
            .order_by(RobotEvaluation.n.desc()) \
            .one()
        last_eval_n = last_eval.n
        # assert that there was only one eval
        assert last_eval_n == 0

        times_query = session.query(RobotState.time_sec, RobotState.time_nsec) \
            .filter(RobotState.evaluation_n == last_eval_n) \
            .order_by(RobotState.time_sec, RobotState.time_nsec) \
            .distinct()

        times = [time for time in times_query]

        for time_sec, time_nsec in times:
            # Account for grace time
            time = float(time_sec) + float(time_nsec) / 1_000_000_000.
            if time <= grace_time:
                continue

            #TODO only do this check every N seconds instead of every single sample

            positions_query = session \
                .query(RobotState.evaluation_robot_id, RobotState.pos_x, RobotState.pos_y) \
                .filter(RobotState.evaluation_n == last_eval_n) \
                .filter(RobotState.evaluation_robot_id.in_(ids)) \
                .filter(RobotState.time_sec == time_sec, RobotState.time_nsec == time_nsec)

            for robot_mother, x, y in positions_query:
                for robot_father, x_f, y_f in positions_query:
                    if robot_mother == robot_father:
                        continue
                    dx: float = x - x_f
                    dy: float = y - y_f
                    distance: float = math.sqrt(dx*dx + dy*dy)
                    if distance < MATING_RANGE:
                        # print(f'MATCH! MOTHER({robot_mother})+FATHER({robot_father}) dist({distance:+2.4f})')
                        individual_map[robot_mother].candidate_partners.add(individual_map[robot_father])

# MATING_RANGE = 0.45
MATING_RANGE = 1

async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 100
    population_size = 100
    offspring_size = population_size

    manage_isaac_multiple.ISOLATED_ENVIRONMENTS = False

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
        mutate_oscillator_amplitude_sigma=0,
        mutate_oscillator_period_sigma=0,
        mutate_oscillator_phase_sigma=0,
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
        for brain_gen in candidate_genotype._brain_genomes:
            if brain_gen._neat_genome.FailsConstraints(neat_conf.multineat_params):
                return False
        return True


    # Parse command line / file input arguments
    args = parser.parse_args()
    experiment_management = ExperimentManagement(args)
    has_offspring = False
    do_recovery = args.recovery_enabled and not experiment_management.experiment_is_new()

    wandb.init(project=f'{args.experiment_name}', entity='revolve', name=f'{args.experiment_name}-{args.run}')

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

    global FITNESS
    try:
        FITNESS = os.environ['FITNESS']
    except KeyError:
        pass

    logger.info(f"Evolving using fitness {FITNESS}.")

    def fitness_function(robot_manager: RobotManager, robot: RevolveBot):
        if FITNESS == 'displacement_velocity':
            return fitness.displacement_velocity(robot_manager, robot)
        elif FITNESS == 'migration':
            # Displacement only on the y axis, signed
            # (so fitness raises when moving on the y axis positively,
            # therefore the population should migrate over time)
            return measures.displacement_velocity_hill(robot_manager)
        elif FITNESS == 'z_depth':
            # No behaviour in fitness, behaviour here influences only mate selection and not explicit fitness
            robot.measure_phenotype()
            return robot._morphological_measurements.z_depth
        else:
            raise RuntimeError(f"FITNESS {FITNESS} not found")


    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=lambda conf, _id: DirectTreeCPGHyperNEATGenotype(conf, _id, random_init_body=True),
        genotype_conf=genotype_conf,
        fitness_function=fitness_function,
        objective_functions=None,
        mutation_operator=lambda genotype, gen_conf: standard_mutation(genotype, gen_conf),
        mutation_conf=genotype_conf,
        crossover_operator=lambda parents, gen_conf, _: standard_crossover(parents, gen_conf),
        crossover_conf=genotype_conf,
        genotype_test=genotype_test_fun,
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

    wandb.config = {
        "experiment": args.experiment_name,
        "run": args.run,
        "recovery": do_recovery,
        "start_generation": gen_num,
        "generations": num_generations,
        "population": population_size,
        "fitness_fun": FITNESS,
        "grace_time": args.grace_time,
        "evaluation_time": args.evaluation_time,
        "dbname": args.dbname,
        "body_morph_single_mutation_prob": morph_single_mutation_prob,
        "body_morph_no_single_mutation_prob": morph_no_single_mutation_prob,
        "body_morph_no_all_mutation_prob": morph_no_all_mutation_prob,
        "body_morph_at_least_one_mutation_prob": morph_at_least_one_mutation_prob,
        "brain_single_mutation_prob": brain_single_mutation_prob,
        "body_max_parts": tree_genotype_conf.max_parts,
        "body_min_parts": tree_genotype_conf.min_parts,
        "body_max_oscillation": tree_genotype_conf.max_oscillation,
        "body_init_n_parts_mu": tree_genotype_conf.init.n_parts_mu,
        "body_init_n_parts_sigma": tree_genotype_conf.init.n_parts_sigma,
        "body_init_prob_no_child": tree_genotype_conf.init.prob_no_child,
        "body_init_prob_child_block": tree_genotype_conf.init.prob_child_block,
        "body_init_prob_child_active_joint": tree_genotype_conf.init.prob_child_active_joint,
        "body_mutation_p_duplicate_subtree": morph_single_mutation_prob,
        "body_mutation_p_delete_subtree": morph_single_mutation_prob,
        "body_mutation_p_generate_subtree": morph_single_mutation_prob,
        "body_mutation_p_swap_subtree": morph_single_mutation_prob,
        "body_mutation_p_mutate_oscillators": brain_single_mutation_prob,
        "body_mutation_p_mutate_oscillator": tree_genotype_conf.mutation.p_mutate_oscillator,
        "body_mutate_oscillator_amplitude_sigma": tree_genotype_conf.mutation.mutate_oscillator_amplitude_sigma,
        "body_mutate_oscillator_period_sigma": tree_genotype_conf.mutation.mutate_oscillator_period_sigma,
        "body_mutate_oscillator_phase_sigma": tree_genotype_conf.mutation.mutate_oscillator_phase_sigma,
    }

    # CELERY CONNECTION (includes database connection)
    # simulator_queue = CeleryQueue(args, args.port_start, dbname='revolve', db_addr='127.0.0.1', use_isaacgym=True)
    simulator_queue = CeleryPopulationQueue(args, use_isaacgym=True, local_computing=True)
    await simulator_queue.start(cleanup_database=(not do_recovery))

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
    population = PositionedPopulation(population_conf, simulator_queue, analyzer_queue, next_robot_id, grid_cell_size=1)

    if do_recovery:
        assert False
        # # loading a previous state of the experiment
        # population.load_snapshot(gen_num, multi_development=True)
        # load_database_ids(gen_num, experiment_management,population.individuals)
        #
        # # drop unfinished db elements
        # with simulator_queue._db.session() as session:
        #     extra_robots = session.query(DBRobot).filter(DBRobot.id >= next_robot_id)
        #     robot_ids: List[int] = [r.id for r in extra_robots]
        #     if len(robot_ids) > 0:
        #         print(f'Dropping unfinished robots (DBIDs={robot_ids})')
        #         session.query(RobotState).filter(RobotState.evaluation_robot_id.in_(robot_ids)).delete()
        #         session.commit()
        #         session.query(RobotEvaluation).filter(RobotEvaluation.robot_id.in_(robot_ids)).delete()
        #         session.commit()
        #         extra_robots.delete()
        #         session.commit()
        # if gen_num >= 0:
        #     logger.info(f'Recovered snapshot {gen_num}, pop with {len(population.individuals)} individuals')
        # if has_offspring:
        #     assert False
        #     individuals = population.load_offspring(gen_num, population_size, offspring_size, next_robot_id)
        #     gen_num += 1
        #     logger.info(f'Recovered unfinished offspring {gen_num}')
        #
        #     if gen_num == 0:
        #         if PROGENITOR:
        #             await population.initialize_from_single_individual(individuals)
        #         else:
        #             await population.initialize(individuals)
        #     else:
        #         population = await population.next_generation(gen_num)
        #
        #     update_robot_pose(population.individuals, simulator_queue._db)
        #     experiment_management.export_snapshots(population.individuals, gen_num)
    elif START_FROM_PREVIOUS_POPULATION:
        experiment_management.create_exp_folders()
        await population.initialize_from_previous_population(
            f"/home/matteo/projects/revolve/experiments/isaac/data/base_test_5_120/{args.run}", 99)
        update_robot_pose(population.individuals, simulator_queue._db)
        experiment_management.export_snapshots(population.individuals, gen_num)
    else:
        # starting a new experiment
        experiment_management.create_exp_folders()
        if PROGENITOR:
            await population.initialize_from_single_individual()
        else:
            await population.initialize()
        update_robot_pose(population.individuals, simulator_queue._db)
        # generate_candidate_partners(population, simulator_queue._db, args.grace_time)
        experiment_management.export_snapshots(population.individuals, gen_num)
        # export_special_data(population.individuals, [], gen_num, simulator_queue._db)
    export_wandb_data(gen_num, population)

    while gen_num < num_generations - 1:
        gen_num += 1
        generate_candidate_partners(population, simulator_queue._db, args.grace_time)
        new_population = await population.next_generation(gen_num)
        update_robot_pose(new_population.individuals, simulator_queue._db)
        with open(f'{experiment_management.generation_folder(gen_num-1)}/database_ids.yml', 'w') as database_id_file:
            save_db_ids(database_id_file, population.individuals)
        experiment_management.export_snapshots(population.individuals, gen_num)
        with open(f'{experiment_management.generation_folder(gen_num-1)}/extra.tsv', 'w') as extra_data_file:
            export_special_data(extra_data_file, population.individuals, new_population.individuals, gen_num, simulator_queue._db)
        export_wandb_data(gen_num, new_population)
        population = new_population

    # CLEANUP
    for celery_worker in celery_workers:
        await celery_worker.stop()
    await simulator_queue.stop()

def save_db_ids(outfile, individuals: List[Individual]):
    database_ids = {}
    for ind in individuals:
        database_ids[ind.phenotype.id] = int(ind.phenotype.database_id)
    yaml.dump(database_ids, outfile)

def load_database_ids(gen_num: int, experiment_management: ExperimentManagement, individuals: List[Individual]):
    database_ids = {}
    with open(f'{experiment_management.generation_folder(gen_num-1)}/database_ids.yml', 'r') as database_id_file:
        database_ids = yaml.safe_load(database_id_file)
    for ind in individuals:
        ind.phenotype.database_id = database_ids[ind.phenotype.id]

def update_robot_pose(individuals: List[Individual], db: PostgreSQLDatabase) -> None:

    with db.session() as session:

        robot: DBRobot = session \
            .query(DBRobot) \
            .filter(DBRobot.name == f'robot_{individuals[0].id}') \
            .one()

        last_eval: RobotEvaluation = session \
            .query(RobotEvaluation) \
            .filter(RobotEvaluation.robot == robot) \
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
            individual.pose = individual.pose.copy()
            individual.pose.x = final_position[0]
            individual.pose.y = final_position[1]


def export_special_data(file, individuals: List[Individual], offspring_list: List[Individual], gen_num: int, db: PostgreSQLDatabase) -> None:
    # write header
    file.write('individual_id\tinitial_position\tfinal_position\tcandidates_best\tcandidates\toffspring_id\n')

    with db.session() as session:
        for individual in individuals:
            dbid = int(individual.phenotype.database_id)

            last_eval: RobotEvaluation = session \
                .query(RobotEvaluation) \
                .filter(RobotEvaluation.robot_id == dbid) \
                .order_by(RobotEvaluation.n.desc()) \
                .one()

            # assert that there was only one eval
            assert last_eval.n == 0

            # Save initial and final positions
            initial_position = session \
                .query(RobotState.pos_x, RobotState.pos_y) \
                .filter(RobotState.evaluation == last_eval) \
                .order_by(RobotState.time_sec.asc(), RobotState.time_nsec.asc()) \
                .first()

            final_position = session \
                .query(RobotState.pos_x, RobotState.pos_y) \
                .filter(RobotState.evaluation == last_eval) \
                .order_by(RobotState.time_sec.desc(), RobotState.time_nsec.desc()) \
                .first()

            # Save candidate lists
            candidates = individual.candidate_partners

            # Save chosen candidate IDs
            # find main offspring
            offspring = None
            for offspring in offspring_list:
                if offspring.parents[0] == individual:
                    break
            assert offspring is not None

            candidates_best = None
            if len(offspring.parents) > 1:
                candidates_best = offspring.parents[1]

            # Write data
            file.write(f'{individual.id}\t{initial_position}\t{final_position}\t{candidates_best}\t{candidates}\t{offspring}\n')

    return


def export_wandb_data(gen_num: int, new_population: PositionedPopulation):
    c_measures = [{
        **i.phenotype._morphological_measurements.measurements_to_dict(),
        **i.phenotype._behavioural_measurements.measurements_to_dict(),
        "fitness": i.fitness,
        "pose_x": i.pose[0],
        "pose_y": i.pose[1],
        "pose_z": i.pose[2],
    }
        for i in new_population.individuals]

    names = c_measures[0].keys()

    for name in names:
        data = np.array([m[name] for m in c_measures])
        wandb.log({
            f'{name}/data': data,
            f'{name}/hist': wandb.Histogram(data),
            f'{name}/mean': np.mean(data),
            f'{name}/median': np.median(data),
            f'{name}/quantile_05%': np.quantile(data, 0.05),
            f'{name}/quantile_25%': np.quantile(data, 0.25),
            f'{name}/quantile_75%': np.quantile(data, 0.75),
            f'{name}/quantile_95%': np.quantile(data, 0.95),
        }, commit=False)

    wandb.log({"generation": gen_num})
