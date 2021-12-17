import tempfile
from typing import Tuple, Optional, AnyStr

import numpy as np
from isaacgym import gymapi
from celery.signals import worker_process_init, worker_process_shutdown

from . import isaac_logger
from pyrevolve.isaac.IsaacSim import IsaacSim
from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase


@worker_process_init.connect
def init_worker_celery(**kwargs):
    global db
    db = init_worker('matteo')


@worker_process_shutdown.connect
def shutdown_worker_celery(**kwargs):
    global db
    shutdown_worker(db)
    db = None


db: Optional[PostgreSQLDatabase] = None


class Arguments:
    def __init__(self,
                 physics_engine=gymapi.SIM_PHYSX,
                 compute_device_id=0,
                 graphics_device_id=0,
                 num_threads=0,
                 headless=True,
                 use_gpu=True):
        self.physics_engine = physics_engine
        self.compute_device_id = compute_device_id
        self.graphics_device_id = graphics_device_id
        self.num_threads = num_threads
        self.headless = headless
        self.use_gpu = use_gpu


def init_worker(dbname: AnyStr, username: AnyStr, password: AnyStr) -> PostgreSQLDatabase:
    isaac_logger.info("Initializing database connection for worker...")
    db_: PostgreSQLDatabase = PostgreSQLDatabase(dbname=dbname, username=username, password=password)
    # Create connection engine
    db_.start_sync()
    isaac_logger.info("DB connection Initialized.")
    return db_


def shutdown_worker(db_: Optional[PostgreSQLDatabase]):
    if db_ is not None:
        # Disconnect from the database
        isaac_logger.info('Closing database connection for worker...')
        db_.disconnect()
        isaac_logger.info('DB connection Closed.')


def init_sym(args: Arguments,
             num_envs: int,
             db: Optional[PostgreSQLDatabase] = None,
             asset_root: Optional[AnyStr] = None) \
        -> Tuple[IsaacSim, gymapi.SimParams]:

    if asset_root is None:
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
        sim_params.physx.use_gpu = args.use_gpu

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

    return gym, sim_params


def simulator_main_loop(gym: IsaacSim, controller_update_time: float):
    # Prepare the simulation
    gym.prepare()

    while True:
        time: float = gym.get_sim_time()
        if time % controller_update_time == 0.0:
            life_cycle(gym, time)
            if len(gym.robots) == 0:
                break
            gym.update_robots(time, controller_update_time)

        # Step the physics
        gym.simulate()
        gym.fetch_results(wait_for_latest_sim_step=True)

        if not gym.is_headless():
            gym.step_graphics()
            gym.draw_viewer()
            gym.sync_frame_time()  # makes the simulator run in real time


def life_cycle(gym: IsaacSim, time: float):
    for i, robot in enumerate(gym.robots):
        if time > robot.death_time():
            isaac_logger.info(f"Robot {robot.name} has finshed evaluation, removing it from the simulator")
            gym.robots.remove(robot)
            # TODO hack your way to remove the robot in simulation, now is only removed from the controller loop
