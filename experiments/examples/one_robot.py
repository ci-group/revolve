import asyncio
import logging
import sys
import os

from pyrevolve import parser
from pyrevolve.custom_logging import logger
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.evolution import fitness


async def run():
    # Parse command line / file input arguments
    settings = parser.parse_args()

    # Start Simulator
    if settings.simulator_cmd != 'debug':
        simulator_supervisor = DynamicSimSupervisor(
            world_file=settings.world,
            simulator_cmd=settings.simulator_cmd,
            simulator_args=["--verbose"],
            plugins_dir_path=os.path.join('.', 'build', 'lib'),
            models_dir_path=os.path.join('.', 'models'),
            simulator_name='gazebo'
        )
        await simulator_supervisor.launch_simulator(port=settings.port_start)
        await asyncio.sleep(0.1)

    # Connect to the simulator and pause
    connection = await World.create(settings, world_address=('127.0.0.1', settings.port_start))
    await asyncio.sleep(1)

    # init finished

    robot_file_path = 'experiments/examples/yaml/spider.yaml'
    robot = RevolveBot()
    robot.load_file(robot_file_path, conf_type='yaml')
    robot.update_substrate()
    robot.save_file(f'{robot_file_path}.sdf', conf_type='sdf')

    await connection.pause(True)
    robot_manager = await connection.insert_robot(robot, Vector3(0, 0, 0.25), life_timeout=None)
    await asyncio.sleep(1.0)

    # Start the main life loop
    while True:
        # Print robot fitness every second
        status = 'dead' if robot_manager.dead else 'alive'
        print(f"Robot fitness ({status}) is \n"
              f" OLD:     {fitness.online_old_revolve(robot_manager)}\n"
              f" DISPLAC: {fitness.displacement(robot_manager, robot)}\n"
              f" DIS_VEL: {fitness.displacement_velocity(robot_manager, robot)}")
        await asyncio.sleep(1.0)
