"""
Loading and testing
"""
from typing import AnyStr

from isaacgym import gymapi
from isaacgym import gymutil

from uuid import uuid4
import math
import numpy as np
import os

from pyrevolve import isaac
from pyrevolve.isaac.Learners import DifferentialEvolution


def simulator(robot_urdf: AnyStr, life_timeout: float) -> int:
    """
    Simulate the robot in isaac gym
    :param robot_urdf: URDF describing the robot
    :param life_timeout: how long should the robot live
    :return: database id of the robot
    """
    filename = f'robot_{uuid4()}.urdf'
    with open('/tmp/'+filename, 'w') as f:
        f.write(robot_urdf)
    # %% Initialize gym
    gym = gymapi.acquire_gym()

    # Parse arguments
    args = gymutil.parse_arguments(description="Loading and testing")

    # configure sim
    sim_params = gymapi.SimParams()
    sim_params.dt = 1.0 / 60.0
    sim_params.substeps = 2

    # defining axis of rotation!
    sim_params.up_axis = gymapi.UP_AXIS_Z
    sim_params.gravity = gymapi.Vec3(0.0, 0.0, -9.8)

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
        sim_params.physx.use_gpu = True

    sim = gym.create_sim(args.compute_device_id, args.graphics_device_id, args.physics_engine, sim_params)

    if sim is None:
        print("*** Failed to create sim")
        quit()

    # Create viewer
    viewer = gym.create_viewer(sim, gymapi.CameraProperties())
    if viewer is None:
        print("*** Failed to create viewer")
        quit()

    #%% Initialize environment
    print("Initialize environment")
    # Add ground plane
    plane_params = gymapi.PlaneParams()
    plane_params.normal = gymapi.Vec3(0, 0, 1) # z-up!
    plane_params.distance = 0
    plane_params.static_friction = 1
    plane_params.dynamic_friction = 1
    plane_params.restitution = 0
    gym.add_ground(sim, plane_params)

    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.flip_visual_attachments = True
    asset_options.armature = 0.01

    # Set up the env grid
    num_envs = 1
    spacing = 50.0
    env_lower = gymapi.Vec3(-spacing, 0.0, -spacing)
    env_upper = gymapi.Vec3(spacing, spacing, spacing)

    # Some common handles for later use
    print("Creating %d environments" % num_envs)
    num_per_row = int(math.sqrt(num_envs))

    pose = gymapi.Transform()
    pose.p = gymapi.Vec3(0, 0, 0.032)
    pose.r = gymapi.Quat(0, 0.0, 0.0, 0.707107)

    # %% Initialize robots: Robot
    print("Initialize Robot")
    # Load robot asset
    asset_root = '/tmp/'
    robot_asset_file = filename

    num_robots = 3
    distance = 1
    robot_handles = []
    envs = []
    # create env
    for i in range(num_envs):
        env = gym.create_env(sim, env_lower, env_upper, num_per_row)
        envs.append(env)

        print("Loading asset '%s' from '%s', #'%i'" % (robot_asset_file, asset_root, i))
        robot_asset = gym.load_asset(
            sim, asset_root, robot_asset_file, asset_options)

        # add robot
        robot_handle = gym.create_actor(env, robot_asset, pose, f"robot #{i}", 0, 0) #(1,2)
        robot_handles.append(robot_handle)

    # get joint limits and ranges for robot
    props = gym.get_actor_dof_properties(env, robot_handle)

    # Give a desired velocity to drive
    props["driveMode"].fill(gymapi.DOF_MODE_POS)
    props["stiffness"].fill(1000.0)
    props["damping"].fill(600.0)
    robot_num_dofs = len(props)

    controller_update_time = sim_params.dt * 10
    controllers = []

    pop_size = num_envs
    assert (pop_size % num_envs == 0)
    genomes = np.random.uniform(0, 1, (pop_size, robot_num_dofs))
    for i in range(num_envs):
        gym.set_actor_dof_properties(envs[i], robot_handles[i], props)
        weights = genomes[i, :]
        controller = isaac.CPG(weights, controller_update_time)
        controllers.append(controller)


    # Point camera at environments
    cam_pos = gymapi.Vec3(-4.0, -1.0, 4.0)
    cam_target = gymapi.Vec3(0.0,-1.0, 2.0)
    gym.viewer_camera_look_at(viewer, None, cam_pos, cam_target)

    # Time to wait in seconds before moving robot
    # next_robot_update_time = 1.5

    # # subscribe to spacebar event for reset
    # gym.subscribe_viewer_keyboard_event(viewer, gymapi.KEY_R, "reset")
    # # create a local copy of initial state, which we can send back for reset
    initial_state = np.copy(gym.get_sim_rigid_body_states(sim, gymapi.STATE_ALL))

    def update_robot():
        for i in range(num_envs):
            controller = controllers[i]
            robot_handle = robot_handles[i]

            position_target = controller.update_CPG().astype('f')
            gym.set_actor_dof_position_targets(envs[i], robot_handle, position_target)

    # %% Initialize learner
    params = {}
    params['evaluate_objective_type'] = 'full'
    params['pop_size'] = pop_size
    params['CR'] = 0.9
    params['F'] = 0.5
    learner = DifferentialEvolution(genomes, num_envs, 'de', (0, 1), params)

    eval_time = life_timeout  # how many seconds should the robot live
    num_gen = 1

    def obtain_fitness(env, body):
        body_states = gym.get_actor_rigid_body_states(env, body, gymapi.STATE_POS)["pose"]["p"][0]
        current_pos = np.array((body_states[0], body_states[1], body_states[2]))
        pose0 = initial_state["pose"]["p"][0]
        original_pos = np.array((pose0[0], pose0[1], pose0[2]))
        absolute_distance = np.linalg.norm(original_pos - current_pos)
        return absolute_distance

    def update_learner():
        print("Update Learner")
        for i in range(num_envs):
            controller = controllers[i]
            robot_handle = robot_handles[i]
            fitness = obtain_fitness(envs[i], robot_handle)
            learner.add_eval(-fitness)

        new_genomes = learner.get_new_weights()
        for i in range(num_envs):
            weights = new_genomes[i, :]
            controller.set_weights(weights)
            controller.reset_controller()
        gym.set_sim_rigid_body_states(sim, initial_state, gymapi.STATE_ALL)

    #%% Simulate
    while not learner.gen == num_gen:
        t = gym.get_sim_time(sim)
        if t % controller_update_time == 0.0:
            if round(t % eval_time, 2) == 0.0 and t > 0.0:
                update_learner()
            update_robot()

        # Step the physics
        gym.simulate(sim)
        gym.fetch_results(sim, True)

        # Step rendering
        gym.step_graphics(sim)
        gym.draw_viewer(viewer, sim, False)
        gym.fetch_results(sim, True)
    gym.destroy_sim(sim)
    return 1
