"""
Loading and testing
"""
import os
import tempfile
from typing import AnyStr, List

from isaacgym import gymapi

from pyrevolve.isaac.ISAACBot import ISAACBot
from pyrevolve.util.supervisor.rabbits import Robot as DBRobot
from pyrevolve.util.supervisor.rabbits import RobotEvaluation as DBRobotEvaluation
from . import isaac_logger
from .IsaacSim import IsaacSim
from .common import init_sym, simulator_main_loop, init_worker, shutdown_worker, Arguments, db


def simulator(robot_urdf: AnyStr, life_timeout: float) -> int:
    """
    Simulate the robot in isaac gym
    :param robot_urdf: URDF describing the robot
    :param life_timeout: how long should the robot live
    :return: database id of the robot
    """
    mydb = db
    # Parse arguments
    # args = gymutil.parse_arguments(description="Loading and testing")
    args = Arguments()
    isolated_environments = True

    manual_db_session = False
    if mydb is None:
        manual_db_session = True
        mydb = init_worker()

    gym: IsaacSim
    sim_params: gymapi.SimParams
    gym, sim_params = init_sym(args, num_envs=1, db=mydb)

    # Load robot asset
    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.flip_visual_attachments = True
    asset_options.armature = 0.01

    robots: List[ISAACBot] = []
    env_indexes: List[int] = []
    robot_asset_files = []

    with mydb.session() as session:
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
        env_index: int = 0

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
        isaac_logger.info(f"Loading {robot.name} asset '{robot_asset_filepath}' from '{asset_root}' ")
        gym.insert_robot(env_index, robot, robot_asset_filename, asset_options, robot.pose, robot.name, 1, 2, 0)

        # Insert robot in the database
        with mydb.session() as session2:
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

    db_robots_id = robot.db_robot_id

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
