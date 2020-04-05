import asyncio
import logging
import os

import sys
import time

from pyrevolve import parser
from pyrevolve.util import logger
from pyrevolve.gazebo.analyze import BodyAnalyzer
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.util.supervisor.supervisor_collision import CollisionSimSupervisor


async def test_collision_robot(robot_file_path: str):
    log = logger.create_logger('experiment', handlers=[
        logging.StreamHandler(sys.stdout),
    ])

    # Set debug level to DEBUG
    log.setLevel(logging.DEBUG)

    # Parse command line / file input arguments
    settings = parser.parse_args()

    assert (settings.test_robot_collision is not None)
    robot = RevolveBot(_id=settings.test_robot_collision)
    robot.load_file(robot_file_path, conf_type='yaml')
    robot.save_file(f'{robot_file_path}.sdf', conf_type='sdf')

    def simulator_died_callback(_process, _ret_code):
        pass

    # Start Simulator
    if settings.simulator_cmd != 'debug':
        simulator_supervisor = CollisionSimSupervisor(
            world_file=os.path.join('tools', 'analyzer', 'analyzer-world.world'),
            simulator_cmd=settings.simulator_cmd,
            simulator_args=["--verbose"],
            plugins_dir_path=os.path.join('.', 'build', 'lib'),
            models_dir_path=os.path.join('.', 'models'),
            simulator_name='gazebo',
            process_terminated_callback=simulator_died_callback,
        )
        await simulator_supervisor.launch_simulator(port=settings.port_start)
        await asyncio.sleep(0.1)

    log.debug("simulator ready")

    # Connect to the simulator and pause
    analyzer = await BodyAnalyzer.create('127.0.0.1', settings.port_start)
    log.debug("connection ready")
    await asyncio.sleep(1)

    log.info("Sending robot to the analyzer simulator")
    start = time.time()
    result = await analyzer.analyze_robot(robot)
    end = time.time()

    log.debug(f'Analyzer finished in {end-start}')
    log.debug('result:')
    log.debug(result)

    await analyzer.disconnect()
    log.debug("disconnected")

    if settings.simulator_cmd != 'debug':
        await simulator_supervisor.stop()

    log.debug("simulator killed")
