import multineat
from isaacgym import gymapi
from isaacgym import gymutil

import math
import numpy as np
import time
import os
from pyrevolve.isaac import CPG
from pyrevolve.isaac.Learners import DifferentialEvolution

# %% Initialize gym
gym = gymapi.acquire_gym()

# Parse arguments
args = gymutil.parse_arguments(description="Loading and testing", headless=True)

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
    sim_params.physx.use_gpu = True

sim = gym.create_sim(args.compute_device_id, -1, args.physics_engine, sim_params)

if sim is None:
    print("*** Failed to create sim")
    quit()

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
num_envs = 1
spacing = 50.0
env_lower = gymapi.Vec3(-spacing, 0.0, -spacing)
env_upper = gymapi.Vec3(spacing, spacing, spacing)

# Some common handles for later use
print("Creating %d environments" % num_envs)
num_per_row = int(math.sqrt(num_envs))

pose = gymapi.Transform()
pose.p = gymapi.Vec3(0, 0.032, 0)
pose.r = gymapi.Quat(-0.707107, 0.0, 0.0, 0.707107)

# create env
env = gym.create_env(sim, env_lower, env_upper, num_per_row)

# Load robot asset
asset_root = os.path.dirname(os.path.abspath(__file__))
robot_asset_file = "salamander.urdf"

num_robots = 1
distance = 5
robot_handles = []
controllers = []
controller_update_time = sim_params.dt * 10
rows = np.floor(np.sqrt(num_robots))
# place robots
# assert (pop_size%num_robots==0)
for i in range(num_robots):
    pose.p = gymapi.Vec3((i % rows) * distance, 0.032, (i // rows) * distance)

    print("Loading asset '%s' from '%s', #%i" % (robot_asset_file, asset_root, i))
    robot_asset = gym.load_asset(
        sim, asset_root, robot_asset_file, asset_options)

    # add robot
    robot_handle = gym.create_actor(env, robot_asset, pose, f"robot_{i}", 0, 0)
    robot_handles.append(robot_handle)

# get joint limits and ranges for robot
props = gym.get_actor_dof_properties(env, robot_handle)

# Give a desired velocity to drive
props["driveMode"].fill(gymapi.DOF_MODE_POS)
props["stiffness"].fill(1000.0)
props["damping"].fill(600.0)
robot_num_dofs = len(props)

genomes = np.random.uniform(0, 1, (num_robots, robot_num_dofs))
for i in range(num_robots):
    gym.set_actor_dof_properties(env, robot_handles[i], props)
    weights = genomes[i, :]
    controller = CPG(weights, controller_update_time)
    controllers.append(controller)

# # subscribe to spacebar event for reset
# # create a local copy of initial state, which we can send back for reset
initial_state = np.copy(gym.get_sim_rigid_body_states(sim, gymapi.STATE_ALL))


def update_robot():
    for i in range(num_robots):
        controller = controllers[i]
        robot_handle = robot_handles[i]

        position_target = controller.update_CPG().astype('f')
        gym.set_actor_dof_position_targets(env, robot_handle, position_target)


# %% Learner
params = {'evaluate_objective_type': 'full',
          'pop_size': num_robots,
          'CR': 0.9,
          'F': 0.5}
learner = DifferentialEvolution(genomes, num_robots, 'de', (0, 1), params)

eval_time = 30
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
    for i in range(num_robots):
        controller = controllers[i]
        robot_handle = robot_handles[i]
        fitness = obtain_fitness(env, robot_handle)
        learner.add_eval(-fitness)

    new_genomes = learner.get_new_weights()
    for i in range(num_robots):
        weights = new_genomes[i, :]
        controller.set_weights(weights)
        controller.reset_controller()
    gym.set_sim_rigid_body_states(sim, initial_state, gymapi.STATE_ALL)


# %% Simulate
while not learner.gen == num_gen:
    t = gym.get_sim_time(sim)
    if t % controller_update_time == 0.0:
        if round(t % eval_time, 2) == 0.0 and t > 0.0:
            update_learner()
        update_robot()

    # Step the physics
    gym.simulate(sim)
    gym.fetch_results(sim, True)

print("Done")
