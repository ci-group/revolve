"""
Loading and testing
"""
from typing import AnyStr, List, Optional
import math
import tempfile
import os

import numpy as np
from isaacgym import gymapi
from isaacgym import gymutil

from pyrevolve import isaac
from pyrevolve.isaac.Learners import DifferentialEvolution

from sqlalchemy.orm import Session

from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase
from pyrevolve.util.supervisor.rabbits import Robot, RobotEvaluation, RobotState

from celery.signals import worker_process_init, worker_process_shutdown

db: Optional[PostgreSQLDatabase] = None


@worker_process_init.connect
def init_worker(**kwargs):
    global db
    print("Initializing database connection for worker...")
    db = PostgreSQLDatabase(username='matteo')
    # Create connection engine
    db.start_sync()
    print("DB connection Initialized.")


@worker_process_shutdown.connect
def shutdown_worker(**kwargs):
    print('Closing database connectionn for worker...')
    # Disconnect from the database
    db.disconnect()
    print('DB connection Closed.')


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

    # %% Initialize gym
    gym = gymapi.acquire_gym()
    print('gym initialized')

    # Parse arguments
    #args = gymutil.parse_arguments(description="Loading and testing")
    args = Arguments()
    print(f'args threads:{args.num_threads} - compute:{args.compute_device_id} - graphics:{args.graphics_device_id} - physics:{args.physics_engine}')

    # Insert robot
    new_robot = Robot(name=robot_asset_filename)
    with db.session() as session:
        assert session.is_active
        session.add(new_robot)  # TODO change to robot name, not random file name
        session.commit()
        # this line actually queries the database while the session is still active
        new_robot_id = new_robot.id

    # configure sim
    sim_params = gymapi.SimParams()
    sim_params.dt = 1.0 / 60.0
    sim_params.substeps = 2
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

    sim = gym.create_sim(args.compute_device_id, args.graphics_device_id, args.physics_engine, sim_params)

    if sim is None:
        print("*** Failed to create sim")
        raise RuntimeError("Failed to create sim")

    if not args.headless:
        viewer = gym.create_viewer(sim, gymapi.CameraProperties())
        # Point camera at environments
        cam_pos = gymapi.Vec3(-4.0, 4.0, -1.0)
        cam_target = gymapi.Vec3(0.0, 2.0, 1.0)
        gym.viewer_camera_look_at(viewer, None, cam_pos, cam_target)

    # %% Initialize environment
    print("Initialize environment")
    # Add ground plane
    plane_params = gymapi.PlaneParams()
    gym.add_ground(sim, plane_params)

    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.flip_visual_attachments = True
    asset_options.armature = 0.01

    # Set up the env grid
    num_envs = 10

    spacing = 2.0
    env_lower = gymapi.Vec3(-spacing, 0.0, -spacing)
    env_upper = gymapi.Vec3(spacing, spacing, spacing)

    # %% Initialize robots: Robot
    print("Initialize Robot")
    # Load robot asset

    print(f"Creating {num_envs} environments")
    envs = []
    num_per_row = int(math.sqrt(num_envs))

    pose = gymapi.Transform()
    pose.p = gymapi.Vec3(0, 0.04, 0)
    pose.r = gymapi.Quat(-0.707107, 0.0, 0.0, 0.707107)

    robot_handles = []
    envs = []
    # create env
    assert(num_envs > 0)
    for i in range(num_envs):
        env = gym.create_env(sim, env_lower, env_upper, num_per_row)
        envs.append(env)

        print(f"Loading asset '{robot_asset_filepath}' from '{asset_root}', #'{i}'")
        robot_asset = gym.load_urdf(
            sim, asset_root, robot_asset_filename, asset_options)

        # add robot
        robot_handle = gym.create_actor(env, robot_asset, pose, f"robot #{i}", 1, 2)
        robot_handles.append(robot_handle)

    # # get joint limits and ranges for robot
    props = gym.get_actor_dof_properties(env, robot_handle)

    # Give a desired velocity to drive
    props["driveMode"].fill(gymapi.DOF_MODE_POS)
    props["stiffness"].fill(1000.0)
    props["damping"].fill(600.0)
    robot_num_dofs = len(props)

    controller_update_time = sim_params.dt * 10
    # List of active controllers
    controllers = []
    # List of active evaluations (database objects)
    evals: List[RobotEvaluation] = []

    pop_size = num_envs
    assert (pop_size % num_envs == 0)
    genomes = np.random.uniform(0, 1, (pop_size, robot_num_dofs))
    for i in range(num_envs):
        gym.set_actor_dof_properties(envs[i], robot_handles[i], props)
        weights = genomes[i, :]
        controller = isaac.CPG(weights, controller_update_time)
        controllers.append(controller)
        evals.append(RobotEvaluation(robot=new_robot, n=i))

    # Write first evaluations in database
    with db.session() as session:
        for e in evals:
            session.add(e)
        session.commit()

    robot_states_session: Session = db.session()

    gym_to_gz_rotation_transform = gymapi.Quat.from_axis_angle(gymapi.Vec3(1, 0, 0), -math.pi/2)

    def update_robot(time: float):
        time_nsec, time_sec = math.modf(time)
        time_nsec *= 1_000_000_000
        for _i in range(num_envs):
            _controller = controllers[_i]
            _robot_handle = robot_handles[_i]

            position_target = _controller.update_CPG().astype('f')
            gym.set_actor_dof_position_targets(envs[_i], _robot_handle, position_target)

            robot_pose = gym.get_actor_rigid_body_states(envs[_i], _robot_handle, gymapi.STATE_POS)["pose"]
            robot_pos: gymapi.Vec3 = robot_pose['p'][0]  # -> [0] is to get the position of the head
            robot_rot: gymapi.Quat = robot_pose['r'][0]  # -> [0] is to get the rotation of the head

            # Convert to gazebo system
            # TODO verify this is correct
            robot_pos_gz = (
                robot_pos[0], -robot_pos[2], robot_pos[1]
            )
            # robot_rot *= gym_to_gz_rotation_transform

            # Save current robot state and queue to the database
            db_state = RobotState(evaluation=evals[_i], time_sec=int(time_sec), time_nsec=int(time_nsec),
                                  # We swap x and z to have the data saved the same way as gazebo
                                  pos_x=float(robot_pos_gz[0]), pos_y=float(robot_pos_gz[1]), pos_z=float(robot_pos_gz[2]),
                                  rot_quaternion_x=float(robot_rot[0]), rot_quaternion_y=float(robot_rot[1]),
                                  rot_quaternion_z=float(robot_rot[2]), rot_quaternion_w=float(robot_rot[3]),
                                  orientation_left=0, orientation_right=0, orientation_forward=0, orientation_back=0)
            robot_states_session.add(db_state)

    # %% Initialize learner
    params = {
        'evaluate_objective_type': 'full',
        'pop_size': pop_size,
        'CR': 0.9,
        'F': 0.5,
    }
    learner = DifferentialEvolution(genomes, num_envs, 'de', (0, 1), params)

    eval_time = life_timeout  # how many seconds should the robot live
    max_num_gen = 10

    def obtain_fitness(env, body):
        body_states = gym.get_actor_rigid_body_states(env, body, gymapi.STATE_POS)["pose"]["p"][0]
        current_pos = np.array((body_states[0], body_states[1], body_states[2]))
        pose0 = initial_state["pose"]["p"][0]
        original_pos = np.array((pose0[0], pose0[1], pose0[2]))
        absolute_distance = np.linalg.norm(original_pos - current_pos)
        return absolute_distance

    def update_learner(gen_counter: int, next_gen: int):
        """

        :param gen_counter:
        :param next_gen:
        :return: False if no running is needed any more
        """
        print("Update Learner")
        with db.session() as session:
            for _i in range(num_envs):
                _controller = controllers[_i]
                _robot_handle = robot_handles[_i]
                fitness = obtain_fitness(envs[_i], robot_handle)
                learner.add_eval(-fitness)
                evals[_i].fitness = float(fitness)
                evals[_i].controller = str(
                    _controller.get_weights())
                session.add(evals[_i])

            if next_gen != max_num_gen:
                new_genomes = learner.get_new_weights()
                for _i in range(num_envs):
                    eval_n = (next_gen*num_envs) + _i
                    _weights = new_genomes[i, :]
                    controller.set_weights(_weights)
                    controller.reset_controller()
                    evals[_i] = RobotEvaluation(robot=new_robot, n=int(eval_n))
                    session.add(evals[_i])

            session.commit()

        gym.set_sim_rigid_body_states(sim, initial_state, gymapi.STATE_ALL)
        return next_gen != max_num_gen

    initial_state = np.copy(gym.get_sim_rigid_body_states(sim, gymapi.STATE_ALL))

    # %% Simulate %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    gym.prepare_sim(sim)
    gym_generation = 1
    running = False
    while not learner.gen == max_num_gen:
        t: float = gym.get_sim_time(sim)
        if t % controller_update_time == 0.0:
            if round(t % eval_time, 2) == 0.0 and t > 0.0:
                # Commit all data of the current robot states into the database
                robot_states_session.commit()
                robot_states_session.close()
                # New generation
                running = update_learner(gym_generation, gym_generation+1)
                if not running:
                    break
                # New generation id
                gym_generation += 1
                # Create robot states session for the new generation
                robot_states_session = db.session()
            update_robot(t)

        # Step the physics
        gym.simulate(sim)
        gym.fetch_results(sim, True)

        if not args.headless:
            gym.step_graphics(sim)
            gym.draw_viewer(viewer, sim, False)
            gym.sync_frame_time(sim)  # makes the simulator run in real time

    # %% END Simulation %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    gym.destroy_sim(sim)

    # remove temporary file
    robot_asset_file.close()

    # close robot states session if present
    robot_states_session.close()
    return new_robot_id
