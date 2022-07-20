"""
Loading and testing
"""
import math
import os
import tempfile
from typing import AnyStr, List, Optional, Callable

import numpy as np
from isaacgym import gymapi

from pyrevolve.isaac.ISAACBot import ISAACBot
from pyrevolve.util.supervisor.rabbits import Robot as DBRobot
from pyrevolve.util.supervisor.rabbits import RobotEvaluation as DBRobotEvaluation
from pyrevolve.util.supervisor.rabbits.fakedb import create_fakedb
from . import isaac_logger
from .IsaacSim import IsaacSim
from .common import init_sym, simulator_main_loop, init_worker, shutdown_worker, Arguments, db

ISOLATED_ENVIRONMENTS: bool = True

def simulator_multiple(robots_urdf: List[AnyStr],
                       life_timeout: float,
                       dbname: AnyStr,
                       dbusername: AnyStr,
                       dbpwd: AnyStr = '',
                       env_constructor: Optional[Callable[[gymapi.Gym, gymapi.Sim, gymapi.Vec3, gymapi.Vec3, int, gymapi.Env], None]] = None) \
        -> List[int]:
    """
    Simulate the robot in isaac gym
    :param robots_urdf: list of URDF describing the robot
    :param life_timeout: how long should the robot live
    :param dbname: name of the database
    :param dbusername: database access username
    :param dbpwd: database access password (optional)
    :param env_constructor: function to build up the environment
    :return: database id of the robot
    """
    mydb = db
    # Parse arguments
    # args = gymutil.parse_arguments(description="Loading and testing")
    try:
        gpu = int(os.environ['GPU_ID'])
    except:
        gpu = 0
    args = Arguments(headless=False, use_gpu=True, compute_device_id=gpu, graphics_device_id=gpu)
    global ISOLATED_ENVIRONMENTS

    manual_db_session = False
    if mydb is None and dbname != 'disabled':
        manual_db_session = True
        mydb = init_worker(dbname, dbusername, dbpwd)
    else:
        mydb = create_fakedb()

    gym: IsaacSim
    sim_params: gymapi.SimParams
    gym, sim_params = init_sym(args, len(robots_urdf) if ISOLATED_ENVIRONMENTS else 1, mydb, None, env_constructor)
    gym.build_environment = env_constructor

    # Load robot asset
    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.flip_visual_attachments = True
    asset_options.armature = 0.01

    num_envs = len(robots_urdf) if ISOLATED_ENVIRONMENTS else 1
    assert (num_envs > 0)

    robots: List[ISAACBot] = []
    env_indexes: List[int] = []
    robot_asset_files = []

    with mydb.session() as session:
        for i, robot_urdf in enumerate(robots_urdf):
            isaac_logger.debug(f'Loading Robot "{i}"')
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
            isaac_logger.debug(f'Loading ISAACBot "{i}"')
            robot: ISAACBot = ISAACBot(robot_urdf, ground_offset=0.04, life_duration=life_timeout)
            env_index: int = i if ISOLATED_ENVIRONMENTS else 0
            isaac_logger.debug(f'Loading ISAACBot "{i}" [DONE]')

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
            if ISOLATED_ENVIRONMENTS:
                env_index = i
            else:
                env_index = 0
                area_size = math.sqrt(len(robots_urdf))
                x: float = math.floor(i % area_size)
                y: float = i // area_size
                robot.pose.p += gymapi.Vec3(x, y, 0)
            if ISOLATED_ENVIRONMENTS:
                gym.insert_robot(env_index, robot, robot_asset_filename, asset_options, robot.pose, f"{robot.name} #{i}", 1, 2, 0)
            else:
                # shared physics collision group
                gym.insert_robot(env_index, robot, robot_asset_filename, asset_options, robot.pose, f"{robot.name} #{i}", 1, 0, 0)
            isaac_logger.info(f"Loaded {robot.name} asset '{robot_asset_filepath}' from '{asset_root}', #'{i}'")

            isaac_logger.debug(f'Loading robot "{i}" on the database')
            # Insert robot in the database
            with mydb.session() as session2:
                robot.db_robot = DBRobot(name=robot.name)
                session2.add(robot.db_robot)
                session2.commit()
                # this line actually queries the database while the session is still active
                robot.db_robot_id = robot.db_robot.id
            isaac_logger.debug(f'Loading robot "{i}" on the database [DONE]')

            db_eval = DBRobotEvaluation(robot=robot.db_robot, n=0)
            robot.evals.append(db_eval)
            # Write first evaluations in database
            session.add(db_eval)
            isaac_logger.debug(f'Loading robot evaluation "{i}" on the database')

        # end for loop
        session.commit()
        isaac_logger.debug(f'Loading all robot evaluations on the database [DONE]')

    db_robots_id = [robot.db_robot_id for robot in gym.robots]

    # %% Simulate %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    controller_update_time = sim_params.dt * 10  # TODO check this is the same as config.py
    # Simulate until all robots died
    simulator_main_loop(gym, controller_update_time)

    # %% END Simulation %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    gym.destroy()

    # remove temporary file
    for robot_asset_file in robot_asset_files:
        robot_asset_file.close()

    if manual_db_session:
        shutdown_worker(mydb)

    return db_robots_id


from multiprocessing import Process, shared_memory


def simulator_multiple_process(robots_urdf: List[AnyStr],
                               life_timeout: float,
                               dbname: AnyStr,
                               dbusername: AnyStr,
                               dbpwd: AnyStr = '',
                               timeout: Optional[float] = None,
                               environment_constructor: Optional[Callable[[gymapi.Gym, gymapi.Sim, gymapi.Vec3, gymapi.Vec3, int, gymapi.Env], None]] = None) -> List[int]:
    """
    Simulate the robot in isaac gym
    :param robots_urdf: URDF describing the robot
    :param life_timeout: how long should the robot live
    :param dbname: name of the database
    :param dbusername: database access username
    :param dbpwd: database access password (optional)
    :param timeout: fail the run if the simulator takes too much time (None means wait indefinitely)
    :param environment_constructor: optional function that gets called whenever a gym environment is initialized
    Function signature is `environment_constructor(gymapi.Gym, gymapi.Sim, gymapi.Vec3, gymapi.Vec3, int, gymapi.Env) -> None`
    :return: database id of the robot
    """
    try:
        result = np.array([0 for _ in range(len(robots_urdf))], dtype=np.int64)
        shared_mem = shared_memory.SharedMemory(create=True, size=result.nbytes)
        process = Process(target=_inner_simulator_multiple_process,
                          args=(robots_urdf, life_timeout, shared_mem.name, dbname, dbusername, dbpwd, environment_constructor))
        process.start()
        process.join(timeout)
        if process.exitcode is None:
            raise RuntimeError(f"Simulation did not finish in {timeout} seconds")
        remote_result = np.ndarray((len(robots_urdf),), dtype=np.int64, buffer=shared_mem.buf)
        result[:] = remote_result[:]
        shared_mem.close()
        shared_mem.unlink()
    except KeyboardInterrupt as e:
        print("Keyboard interrupt: CTR-C Detected. Closing shared memory")
        shared_mem.close()
        shared_mem.unlink()
        exit()
    return result


def _inner_simulator_multiple_process(robots_urdf: List[AnyStr],
                                      life_timeout: float,
                                      shared_mem_name: AnyStr,
                                      dbname: AnyStr,
                                      dbusername: AnyStr,
                                      dbpwd: AnyStr = '',
                                      environment_constructor: Optional[Callable[[gymapi.Gym, gymapi.Sim, gymapi.Vec3, gymapi.Vec3, int, gymapi.Env], None]] = None) -> int:
    robot_ids: List[int] = simulator_multiple(robots_urdf, life_timeout, dbname, dbusername, dbpwd, environment_constructor)
    robot_ids = np.array(robot_ids)
    existing_shared_mem = shared_memory.SharedMemory(name=shared_mem_name)
    remote_result = np.ndarray((len(robots_urdf),), dtype=np.int64, buffer=existing_shared_mem.buf)
    remote_result[:] = robot_ids[:]
    existing_shared_mem.close()
    return 0
