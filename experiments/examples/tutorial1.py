#!/usr/bin/env python3
import asyncio
import os
from pyrevolve import parser
from pyrevolve.gazebo.manage import WorldManager as World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.custom_logging.logger import logger


async def run():
    logger.info('Hello World!')
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

    connection = await World.create()
    if connection:
        logger.info("Connected to the simulator world.")

    await connection.pause(True)

    while True:
        await asyncio.sleep(10.0)
