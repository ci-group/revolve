"""
Loading and testing
"""
import math
import os
import random
import tempfile
import threading
from typing import AnyStr, List, Optional

import numpy as np
from celery.signals import worker_process_init, worker_process_shutdown
from isaacgym import gymapi
from sqlalchemy.orm import Session

from pyrevolve.isaac.ISAACBot import ISAACBot
from pyrevolve.revolve_bot.brain.controller import Controller as RevolveController, DifferentialCPG, \
    DifferentialCPG_ControllerParams
from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase
from pyrevolve.util.supervisor.rabbits import Robot as DBRobot
from pyrevolve.util.supervisor.rabbits import RobotEvaluation as DBRobotEvaluation
from pyrevolve.util.supervisor.rabbits import RobotState as DBRobotState
from . import isaac_logger
from .IsaacSim import IsaacSim


class Arguments:
    def __init__(self):
        self.physics_engine = gymapi.SIM_PHYSX
        self.compute_device_id = 0
        self.graphics_device_id = 0
        self.num_threads = 0
        self.headless = True


@worker_process_init.connect
def init_worker_celery(**kwargs):
    init_worker()


@worker_process_shutdown.connect
def shutdown_worker_celery(**kwargs):
    shutdown_worker()


db: Optional[PostgreSQLDatabase] = None
gym: Optional[IsaacSim] = None
sim_params: Optional[gymapi.SimParams]
sim_thread: threading.Thread
stop_simulator: bool = True


def init_worker():
    global db, gym, sim_params, sim_thread, stop_simulator
    isaac_logger.info("Initializing database connection for worker...")
    db = PostgreSQLDatabase(username='matteo')
    # Create connection engine
    db.start_sync()
    isaac_logger.info("DB connection Initialized.")

    asset_root = tempfile.gettempdir()

    # Parse arguments
    # args = gymutil.parse_arguments(description="Loading and testing")
    args = Arguments()

    num_envs = 1

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

    gym = IsaacSim(db, asset_root,
                   args.compute_device_id, args.graphics_device_id, args.physics_engine, sim_params,
                   args.headless,
                   num_envs, 2.0)
    isaac_logger.debug('gym initialized')

    # %% Initialize environment
    isaac_logger.debug("Initialize environment")
    # Add ground plane
    plane_params = gymapi.PlaneParams()
    plane_params.normal = gymapi.Vec3(0, 0, 1)  # z-up!
    gym.add_ground(plane_params)

    # Start the simulation thread
    stop_simulator = False
    sim_thread = threading.Thread(target=simulator_main_loop, args=(args.headless,))
    sim_thread.start()


def shutdown_worker():
    global db, gym, sim_thread, stop_simulator
    stop_simulator = True
    sim_thread.join(10.0)  # wait ten seconds to shutdown
    if sim_thread.is_alive():
        isaac_logger.error("Simulator not terminated after 10 seconds of waiting, giving up.")
        # standard python cannot force close a thread, and you should really not to (or GIL and GC could have problems)
    if gym is not None:
        gym.destroy()
    if db is not None:
        # Disconnect from the database
        isaac_logger.info('Closing database connection for worker...')
        db.disconnect()
        isaac_logger.info('DB connection Closed.')
        db = None


def simulator_main_loop(headless):
    global db, gym, sim_params, stop_simulator
    controller_update_time = sim_params.dt * 10

    # Prepare the simulation
    gym.prepare()

    while not stop_simulator:
        t: float = gym.get_sim_time()
        if t % controller_update_time == 0.0:
            life_cycle()
            gym.update_robots(t, controller_update_time)

        # Step the physics
        gym.simulate()
        gym.fetch_results(wait_for_latest_sim_step=True)

        if not headless:
            gym.step_graphics()
            gym.draw_viewer()
            gym.sync_frame_time()  # makes the simulator run in real time


def life_cycle(time: float):
    global db, gym, sim_params, stop_simulator
    for i, robot in enumerate(gym.robots):
        if time > robot.death_time():
            isaac_logger.info(f"Robot {robot.name} has finshed evaluation, removing it from the simulator")
            gym.robots.remove(robot)


def simulator_multiple(robots_urdf: List[AnyStr], life_timeout: float) -> int:
    """
    Simulate the robot in isaac gym
    :param robots_urdf: list of URDF describing the robot
    :param life_timeout: how long should the robot live
    :return: database id of the robot
    """
    global gym, sim_params
    # Create temporary file for the robot urdf. The file will be removed when the file is closed.

    init_worker()

    # Load robot asset
    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.flip_visual_attachments = True
    asset_options.armature = 0.01

    isolated_environments = False
    num_envs = len(robots_urdf) if isolated_environments else 1
    assert (num_envs > 0)

    robots: List[ISAACBot] = []
    env_indexes: List[int] = []
    robot_asset_files = []

    with db.session() as session:
        for i, robot_urdf in enumerate(robots_urdf):
            # TODO place the tempfiles in a separate temporary folder for all assets.
            #  I.e. `tmp_asset_dir = tempfile.TemporaryDirectory(prefix='revolve_')`
            robot_asset_file = tempfile.NamedTemporaryFile(mode='w+t', prefix='revolve_isaacgym_robot_urdf_', suffix='.urdf')
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
            env_index: int = i if isolated_environments else 1

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
            gym.insert_robot(i, robot, robot_asset_filename, asset_options, robot.pose, f"{robot.name} #{i}", 1, 2, 0)

            # Insert robot in the database
            robot.db_robot = DBRobot(name=robot.name)
            assert session.is_active
            session.add(robot.db_robot)
            # this line actually queries the database while the session is still active
            db_robot_id = robot.db_robot.id

            db_eval = DBRobotEvaluation(robot=robot.db_robot, n=0)
            robot.evals.append(db_eval)
            # Write first evaluations in database
            session.add(db_eval)

        # end for loop
        session.commit()

    # def obtain_fitness(env_, robot_handle_):
    #     body_states = gym.get_robot_position_rotation(env_, robot_handle_)[0]
    #     current_pos = np.array((body_states[0], body_states[1], body_states[2]))
    #     initial_state = initial_states[(env_, robot_handle_)]
    #     position0 = initial_state[0]
    #     original_pos = np.array((position0[0], position0[1], position0[2]))
    #     absolute_distance = np.linalg.norm(original_pos - current_pos)
    #     return absolute_distance

    initial_states = {}
    for env in gym.envs:
        for r in gym.robot_handles:
            initial_states[(env, r)] = np.copy(gym.get_robot_position_rotation(env, r))

    # %% Simulate %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    # WAIT FOR THREAD


    # %% END Simulation %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    shutdown_worker()

    # remove temporary file
    for robot_asset_file in robot_asset_files:
        robot_asset_file.close()

    return db_robot_id
