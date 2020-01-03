#!/usr/bin/env python3

import os
import sys
import asyncio
from pyrevolve.SDF.math import Vector3
from pyrevolve import revolve_bot, parser
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.evolution import fitness

from pycelery.tasks import random_fitness, increasing_fitness, stupid

async def run():
    """
    The main coroutine, which is started below.
    """
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

    # Load a robot from yaml
    robot = revolve_bot.RevolveBot()
    robot.load_file(robot_file_path)
    robot.update_substrate()
    # robot._brain = BrainRLPowerSplines()

    # Connect to the simulator and pause
    connection = await World.create(settings, world_address=('127.0.0.1', settings.port_start))
    await asyncio.sleep(1)

    # Starts the simulation
    await connection.pause(False)

    # Insert the robot in the simulator
    robot_manager = await connection.insert_robot(robot, Vector3(0, 0, settings.z_start))

    # Start a run loop to do some stuff
    x=0
    while True:
        # Print robot fitness every second
        status = 'dead' if robot_manager.dead else 'alive'
        x = increasing_fitness.delay(x).get()

        print(f"Robot fitness ({status}) is \n"
              f" Stupid:  {stupid.delay().get()}\n"
              f" Random: {random_fitness.delay().get()}\n"
              f" Increasing: {x}")

        await asyncio.sleep(1.0)
