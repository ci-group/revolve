"""
Loading and testing
"""
import math
import os
import random
import tempfile
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


def shutdown_worker():
    global db
    if db is not None:
        # Disconnect from the database
        isaac_logger.info('Closing database connection for worker...')
        db.disconnect()
        isaac_logger.info('DB connection Closed.')
        db = None


class Arguments:
    def __init__(self):
        self.physics_engine = gymapi.SIM_PHYSX
        self.compute_device_id = 0
        self.graphics_device_id = 0
        self.num_threads = 0
        self.headless = True


def simulator(robot_urdf: AnyStr, life_timeout: float) -> int:
    """
    Simulate the robot in isaac gym
    :param robot_urdf: URDF describing the robot
    :param life_timeout: how long should the robot live
    :return: database id of the robot
    """
    # Create temporary file for the robot urdf. The file will be removed when the file is closed.
    # TODO place the tempfiles in a separate temporary folder for all assets.
    #  I.e. `tmp_asset_dir = tempfile.TemporaryDirectory(prefix='revolve_')`
    robot_asset_file = tempfile.NamedTemporaryFile(mode='w+t', prefix='revolve_isaacgym_robot_urdf_', suffix='.urdf')

    # Path of the file created, to pass to the simulator.
    robot_asset_filepath: AnyStr = robot_asset_file.name
    asset_root: AnyStr = os.path.dirname(robot_asset_filepath)
    robot_asset_filename: AnyStr = os.path.basename(robot_asset_filepath)

    # Write URDF to temp file
    robot_asset_file.write(robot_urdf)
    robot_asset_file.flush()


    # Parse arguments
    #args = gymutil.parse_arguments(description="Loading and testing")
    args = Arguments()
    isaac_logger.debug(
        f'args threads:{args.num_threads} - compute:{args.compute_device_id} - graphics:{args.graphics_device_id} - physics:{args.physics_engine}')

    # Parse URDF(xml) locally, we need to extract some data
    robot: ISAACBot = ISAACBot(robot_urdf)

    manual_db_session = False
    if db is None:
        manual_db_session = True
        init_worker()

    # Insert robot
    db_robot = DBRobot(name=robot.name)
    with db.session() as session:
        assert session.is_active
        session.add(db_robot)
        session.commit()
        # this line actually queries the database while the session is still active
        db_robot_id = db_robot.id

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

    num_envs = 1

    # %% Initialize gym
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

    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.flip_visual_attachments = True
    asset_options.armature = 0.01

    # %% Initialize robots: Robot
    isaac_logger.debug("Initialize Robot")
    # Load robot asset

    # put robots in environments
    assert (num_envs > 0)
    for i in range(num_envs):
        isaac_logger.info(f"Loading {robot.name} asset '{robot_asset_filepath}' from '{asset_root}', #'{i}'")
        gym.insert_robot(i, robot, robot_asset_filename, asset_options, robot.pose, f"{robot.name} #{i}", 1, 2, 0)

    controller_update_time = sim_params.dt * 10
    # List of active controllers
    controllers = []
    # List of active evaluations (database objects)
    evals: List[DBRobotEvaluation] = []

    controller_urdf = robot.controller_desc()
    learner_type = robot.learner_desc().getAttribute('type')

    controller_type = controller_urdf.getAttribute('type')
    if controller_type == 'cpg':
        Controller = lambda args: DifferentialCPG(args[0], args[1])
        params = DifferentialCPG_ControllerParams()
        for key, value in controller_urdf.attributes.items():
            if not hasattr(params, key):
                print(f"{controller_type}-controller has no parameter: {key}")
                continue
            try:
                if key == 'weights':
                    value = f"[{value.replace(';', ',')}]"
                setattr(params, key, eval(value))
            except:
                print(f"URDF parameter {key} has invalid value {value} -> requires type: {type(params.__getattribute__(key))}")
        if not params.weights:
            params.weights = [random.uniform(0, 1) for _ in range(robot.n_weights)]
        matrix = robot.create_CPG_network(params.weights)
        controller_init_params = (
            params,
            robot.actuators
        )
    elif controller_type == 'cppn-cpg':
        Controller = lambda args: DifferentialCPG(args[0], args[1])
        # TODO load parameters from URDF element
        params = DifferentialCPG_ControllerParams()
        params.weights = [random.uniform(0, 1) for _ in range(robot.n_weights)]
        controller_init_params = (
            params,
            robot.actuators
        )
    else:
        raise RuntimeError(f'unsupported controller "{controller_type}"')

    isaac_logger.info(f'Loading Controller "{controller_type}" with learner "{learner_type}" [LEARNING NOT IMPLEMENTED]')

    for i in range(num_envs):
        controller = Controller(controller_init_params)
        controllers.append(controller)
        evals.append(DBRobotEvaluation(robot=db_robot, n=i))

    # Write first evaluations in database
    with db.session() as session:
        for e in evals:
            session.add(e)
        session.commit()

    robot_states_session: Session = db.session()

    def update_robot(time: float, delta: float):
        time_nsec, time_sec = math.modf(time)
        time_nsec *= 1_000_000_000
        for _i in range(num_envs):
            _robot_handle = gym.robot_handles[_i]
            controller: RevolveController = controllers[_i]
            # controller: RevolveController = gym.controllers[_robot_handle]

            controller.update(robot.actuators, robot.sensors, time, delta)

            position_target = np.array([act.output for act in robot.actuators]).astype('f')
            gym.set_robot_dof_position_targets(gym.envs[_i], _robot_handle, position_target[robot.actuator_map])

            robot_pose = gym.get_robot_position_rotation(gym.envs[i], _robot_handle)
            robot_pos: gymapi.Vec3 = robot_pose[0]
            robot_rot: gymapi.Quat = robot_pose[1]

            # Save current robot state and queue to the database
            db_state = DBRobotState(evaluation=evals[_i], time_sec=int(time_sec), time_nsec=int(time_nsec),
                                    # We swap x and z to have the data saved the same way as gazebo
                                    pos_x=float(robot_pos[0]),
                                    pos_y=float(robot_pos[1]),
                                    pos_z=float(robot_pos[2]),
                                    rot_quaternion_x=float(robot_rot[0]), rot_quaternion_y=float(robot_rot[1]),
                                    rot_quaternion_z=float(robot_rot[2]), rot_quaternion_w=float(robot_rot[3]),
                                    orientation_left=0, orientation_right=0, orientation_forward=0, orientation_back=0)
            robot_states_session.add(db_state)

    eval_time = life_timeout  # how many seconds should the robot live

    def obtain_fitness(env_, robot_handle_):
        body_states = gym.get_robot_position_rotation(env_, robot_handle_)[0]
        current_pos = np.array((body_states[0], body_states[1], body_states[2]))
        initial_state = initial_states[(env_, robot_handle_)]
        position0 = initial_state[0]
        original_pos = np.array((position0[0], position0[1], position0[2]))
        absolute_distance = np.linalg.norm(original_pos - current_pos)
        return absolute_distance

    initial_states = {}
    for env in gym.envs:
        for r in gym.robot_handles:
            initial_states[(env, r)] = np.copy(gym.get_robot_position_rotation(env, r))

    # %% Simulate %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    gym.prepare()

    while True:
        t: float = gym.get_sim_time()
        if t % controller_update_time == 0.0:
            if round(t % eval_time, 2) == 0.0 and t > 0.0:
                break
            else:
                update_robot(t, controller_update_time)

        # Step the physics
        gym.simulate()
        gym.fetch_results(wait_for_latest_sim_step=True)

        if not args.headless:
            gym.step_graphics()
            gym.draw_viewer()
            gym.sync_frame_time()  # makes the simulator run in real time

    # %% END Simulation %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    # Commit all data of the current robot states into the database
    robot_states_session.commit()
    robot_states_session.close()

    with db.session() as session:
        _controller = controllers[0]
        fitness = obtain_fitness(gym.envs[0], gym.robot_handles[0])
        evals[0].fitness = float(fitness)
        # evals[0].controller = str(
        #     _controller.get_weights())
        session.add(evals[0])
        session.commit()

    gym.destroy()

    # remove temporary file
    robot_asset_file.close()

    # close robot states session if present
    robot_states_session.close()

    if manual_db_session:
        shutdown_worker()

    return db_robot_id
