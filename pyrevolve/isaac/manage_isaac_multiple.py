"""
Loading and testing
"""
import os
import tempfile
from typing import AnyStr, List, Optional, Tuple

import numpy as np
from celery.signals import worker_process_init, worker_process_shutdown
from isaacgym import gymapi

from pyrevolve.isaac.ISAACBot import ISAACBot
from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase
from pyrevolve.util.supervisor.rabbits import Robot as DBRobot
from pyrevolve.util.supervisor.rabbits import RobotEvaluation as DBRobotEvaluation
from . import isaac_logger
from .IsaacSim import IsaacSim


class Arguments:
    def __init__(self):
        self.physics_engine = gymapi.SIM_PHYSX
        self.compute_device_id = 0
        self.graphics_device_id = 0
        self.num_threads = 0
        self.headless = False


@worker_process_init.connect
def init_worker_celery(**kwargs):
    init_worker()


@worker_process_shutdown.connect
def shutdown_worker_celery(**kwargs):
    shutdown_worker()


db: Optional[PostgreSQLDatabase] = None


def init_worker():
    global db
    isaac_logger.info("Initializing database connection for worker...")
    db = PostgreSQLDatabase(username='matteo')
    # Create connection engine
    db.start_sync()
    isaac_logger.info("DB connection Initialized.")


def init_sym(_db: PostgreSQLDatabase, args: Arguments, num_envs: int) -> Tuple[IsaacSim, gymapi.SimParams]:
    assert _db is not None
    asset_root = tempfile.gettempdir()

    # configure sim
    sim_params = gymapi.SimParams()
    sim_params.dt = 1.0 / 60.0
    sim_params.substeps = 2
    sim_params.up_axis = gymapi.UP_AXIS_Z
    sim_params.gravity = gymapi.Vec3(0.0, 0.0, -9.81)
    if args.physics_engine == gymapi.SIM_FLEX:
        sim_params.flex.solver_type = 5
        sim_params.flex.num_outer_iterations = 4
        sim_params.flex.num_inner_iterations = 15
        sim_params.flex.relaxation = 0.75
        sim_params.flex.warm_start = 0.8
    elif args.physics_engine == gymapi.SIM_PHYSX:
        sim_params.physx.solver_type = 1
        sim_params.physx.num_position_iterations = 4
        sim_params.physx.num_velocity_iterations = 1
        sim_params.physx.num_threads = args.num_threads
        sim_params.physx.use_gpu = False

    isaac_logger.debug(
        f'args threads:{args.num_threads} - compute:{args.compute_device_id} - graphics:{args.graphics_device_id} - physics:{args.physics_engine}')

    gym = IsaacSim(_db, asset_root,
                   args.compute_device_id, args.graphics_device_id, args.physics_engine, sim_params,
                   args.headless,
                   num_envs, 0.5)
    isaac_logger.debug('gym initialized')

    # %% Initialize environment
    isaac_logger.debug("Initialize environment")
    # Add ground plane
    plane_params = gymapi.PlaneParams()
    plane_params.normal = gymapi.Vec3(0, 0, 1)  # z-up!
    gym.add_ground(plane_params)

    return gym, sim_params


def shutdown_worker():
    global db
    if db is not None:
        # Disconnect from the database
        isaac_logger.info('Closing database connection for worker...')
        db.disconnect()
        isaac_logger.info('DB connection Closed.')
        db = None


def simulator_main_loop(gym: IsaacSim, controller_update_time: float, headless):
    global db

    # Prepare the simulation
    gym.prepare()

    while True:
        time: float = gym.get_sim_time()
        if time % controller_update_time == 0.0:
            life_cycle(gym, time)
            if len(gym.robots) is 0:
                break
            gym.update_robots(time, controller_update_time)

        # Step the physics
        gym.simulate()
        gym.fetch_results(wait_for_latest_sim_step=True)

        if not headless:
            gym.step_graphics()
            gym.draw_viewer()
            gym.sync_frame_time()  # makes the simulator run in real time


def life_cycle(gym: IsaacSim, time: float):
    global db
    for i, robot in enumerate(gym.robots):
        if time > robot.death_time():
            isaac_logger.info(f"Robot {robot.name} has finshed evaluation, removing it from the simulator")
            gym.robots.remove(robot)
            # TODO hack your way to remove the robot in simulation, now is only removed from the controller loop


def simulator_multiple(robots_urdf: List[AnyStr], life_timeout: float) -> List[int]:
    """
    Simulate the robot in isaac gym
    :param robots_urdf: list of URDF describing the robot
    :param life_timeout: how long should the robot live
    :return: database id of the robot
    """
    global db

    # Parse arguments
    # args = gymutil.parse_arguments(description="Loading and testing")
    args = Arguments()
    isolated_environments = True

    manual_db_session = False
    if db is None:
        manual_db_session = True
        init_worker()

    gym: IsaacSim
    sim_params: gymapi.SimParams
    gym, sim_params = init_sym(db, args, len(robots_urdf) if isolated_environments else 1)

    # Load robot asset
    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.flip_visual_attachments = True
    asset_options.armature = 0.01

    num_envs = len(robots_urdf) if isolated_environments else 1
    assert (num_envs > 0)

    robots: List[ISAACBot] = []
    env_indexes: List[int] = []
    robot_asset_files = []

    with db.session() as session:
        for i, robot_urdf in enumerate(robots_urdf):
            # Create temporary file for the robot urdf. The file will be removed when the file is closed.
            # TODO place the tempfiles in a separate temporary folder for all assets.
            #  I.e. `tmp_asset_dir = tempfile.TemporaryDirectory(prefix='revolve_')`
            robot_asset_file = tempfile.NamedTemporaryFile(mode='w+t',
                                                           prefix='revolve_isaacgym_robot_urdf_',
                                                           suffix='.urdf')
            robot_asset_files.append(robot_asset_file)

            # Path of the file created, to pass to the simulator.
            robot_asset_filepath: AnyStr = robot_asset_file.name
            asset_root: AnyStr = os.path.dirname(robot_asset_filepath)
            robot_asset_filename: AnyStr = os.path.basename(robot_asset_filepath)

            # Write URDF to temp file
            robot_asset_file.write(robot_urdf)
            robot_asset_file.flush()

            # Parse URDF(xml) locally, we need to extract some data
            robot: ISAACBot = ISAACBot(robot_urdf, ground_offset=0.04, life_duration=life_timeout)
            env_index: int = i if isolated_environments else 0

            # Controller
            controller_type = robot.controller_desc().getAttribute('type')
            learner_type = robot.learner_desc().getAttribute('type')

            isaac_logger.info(
                f'Loading Controller "{controller_type}" with learner "{learner_type}" [LEARNING NOT IMPLEMENTED]')

            # %% Initialize robots: Robot
            isaac_logger.debug("Initialize Robot")

            robots.append(robot)
            env_indexes.append(env_index)

            # Load in the simulator
            isaac_logger.info(f"Loading {robot.name} asset '{robot_asset_filepath}' from '{asset_root}', #'{i}'")
            if isolated_environments:
                env_index = i
            else:
                env_index = 0
                robot.pose += gymapi.Vec3(
                    gym.en
                )
            gym.insert_robot(env_index, robot, robot_asset_filename, asset_options, robot.pose, f"{robot.name} #{i}", 1, 2, 0)

            # Insert robot in the database
            with db.session() as session2:
                robot.db_robot = DBRobot(name=robot.name)
                session2.add(robot.db_robot)
                session2.commit()
                # this line actually queries the database while the session is still active
                robot.db_robot_id = robot.db_robot.id

            db_eval = DBRobotEvaluation(robot=robot.db_robot, n=0)
            robot.evals.append(db_eval)
            # Write first evaluations in database
            session.add(db_eval)

        # end for loop
        session.commit()

    db_robots_id = [robot.db_robot_id for robot in gym.robots]

    # %% Simulate %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    controller_update_time = sim_params.dt * 10
    # Simulate until all robots died
    simulator_main_loop(gym, controller_update_time, args.headless)

    # %% END Simulation %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    gym.destroy()

    # remove temporary file
    for robot_asset_file in robot_asset_files:
        robot_asset_file.close()

    if manual_db_session:
        shutdown_worker()

    return db_robots_id
