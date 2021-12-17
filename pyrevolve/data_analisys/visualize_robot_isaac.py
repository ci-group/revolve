import argparse
import logging
import os
from typing import AnyStr

from pyrevolve.isaac.ISAACBot import ISAACBot
from pyrevolve.isaac.IsaacSim import IsaacSim
from pyrevolve.isaac.common import init_sym, Arguments, simulator_main_loop
from pyrevolve.revolve_bot import RevolveBot
from thirdparty.isaacgym.python.isaacgym import gymapi


def test_robot_run_isaac(robot_file_path: AnyStr, log: logging.Logger, settings: argparse.Namespace):


    # Load robot asset
    asset_options = gymapi.AssetOptions()
    asset_options.fix_base_link = False
    asset_options.flip_visual_attachments = True
    asset_options.armature = 0.01

    robot = RevolveBot(_id=settings.test_robot)
    robot.load_file(robot_file_path, conf_type='yaml')
    robot.update_substrate()
    robot_asset_filepath = f'{robot_file_path}.urdf'
    # robot.save_file(robot_asset_filepath, conf_type='urdf')
    robot_urdf = robot.to_urdf(nice_format=True)

    asset_root: AnyStr = os.path.dirname(robot_asset_filepath)
    robot_asset_filename: AnyStr = os.path.basename(robot_asset_filepath)

    with open(robot_asset_filepath, 'w') as f:
        f.write(robot_urdf)

    isaac_robot: ISAACBot = ISAACBot(robot_urdf, ground_offset=0.04)

    # Controller
    controller_type = isaac_robot.controller_desc().getAttribute('type')
    learner_type = isaac_robot.learner_desc().getAttribute('type')
    print(f'Loading Controller "{controller_type}" with learner "{learner_type}"')

    args = Arguments(headless=not settings.gui)

    gym: IsaacSim
    sim_params: gymapi.SimParams
    gym, sim_params = init_sym(args, num_envs=1, db=None, asset_root=asset_root)

    print(f"Loading {isaac_robot.name} asset '{robot_asset_filepath}' from '{asset_root}'")
    gym.insert_robot(0, isaac_robot, robot_asset_filename, asset_options, isaac_robot.pose, isaac_robot.name, 1, 2, 0)
    print(f"Loaded {isaac_robot.name} asset '{robot_asset_filepath}' from '{asset_root}'")

    controller_update_time = sim_params.dt * 10
    try:
        simulator_main_loop(gym, controller_update_time)
    finally:
        gym.destroy()
