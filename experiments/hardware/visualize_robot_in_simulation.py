"""
This script loads a robot.yaml file in simulation and sets all of the servos to -1

This is useful to create the hardware configuration for the robot, to set the inversion of the servos correctly.
"""
import asyncio
import os
import sys

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
sys.path.append(newpath)

from pyrevolve.SDF.math import Vector3
from pyrevolve.revolve_bot.brain.fixed_angle import FixedAngleBrain
from pyrevolve import revolve_bot, parser
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor


async def run():
    robot_file_path = "experiments/examples/yaml/spider.yaml"

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

    robot = RevolveBot(_id=settings.test_robot)
    robot.load_file(robot_file_path, conf_type='yaml')
    robot._brain = FixedAngleBrain(-1)

    await connection.pause(True)
    robot_manager = await connection.insert_robot(robot, Vector3(0, 0, 0.25), life_timeout=None)
    await asyncio.sleep(1.0)

    # Start the main life loop
    while True:
        try:
            await asyncio.sleep(1.0)
        except InterruptedError:
            break
