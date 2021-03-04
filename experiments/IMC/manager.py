import asyncio
import logging
import sys
import os

from pygazebo.connection import DisconnectError
from pyrevolve import parser
from pyrevolve.custom_logging import logger
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.SDF.math import Vector3
# from pyrevolve.tol.manage import World
from pyrevolve.tol.manage.single_robot_world import SingleRobotWorld as World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor


async def run():
    """
    The main coroutine, which is started below
    """
    log = logger.create_logger('experiment', handlers=[
        logging.StreamHandler(sys.stdout),
    ])

    # Set debug level to DEBUG
    log.setLevel(logging.DEBUG)

    # Parse command line / file input arguments
    settings = parser.parse_args()


    # Start Simulator
    if settings.simulator_cmd != 'debug':
        simulator_supervisor = DynamicSimSupervisor(
            world_file=settings.world,
            simulator_cmd=settings.simulator_cmd,
            simulator_args=["--verbose"],
            # simulator_args=[""]
            plugins_dir_path=os.path.join('.', 'build', 'lib'),
            models_dir_path=os.path.join('.', 'models'),
            simulator_name='/home/fuda/Projects/gazebo/build/gazebo/gzserver'   # /home/fuda/Projects/gazebo/build/gazebo/gzserver
        )
    await simulator_supervisor.launch_simulator(port=settings.port_start)
    await asyncio.sleep(0.1)


    # Connect to the simulator and pause
    connection = await World.create(settings, world_address=('127.0.0.1', settings.port_start))
    await asyncio.sleep(1)
    await connection.pause(True)
    await connection.reset(True)

    # initialization finished

    # load robot file
    robot = RevolveBot()

    # robot_file_path = "experiments/IMC/yaml/Single_link.yaml"   #single link testing
    # robot_file_path = "experiments/IMC/yaml/IMC_667710.yaml"        #sven
    # robot_file_path = "experiments/IMC/yaml/IMC_babyA4.yaml"
    # robot_file_path = "experiments/IMC/yaml/IMC_babyB9.yaml"
    # robot_file_path = "experiments/IMC/yaml/IMC_gecko5.yaml"        #sven8
    robot_file_path = "experiments/IMC/yaml/IMCspider.yaml"        #sven
    # robot_file_path = "experiments/IMC/yaml/IMC_spider9.yaml"        #spider9

    robot.load_file(robot_file_path, conf_type='yaml')
    robot.update_substrate()
    robot.save_file(f'{robot_file_path}.sdf', conf_type='sdf')

    # insert robot into the simulator
    robot_manager = await connection.insert_robot(robot, Vector3(0, 0, 0.05), life_timeout=None)
    await connection.pause(False)

    # Start the main life loop
    while True:
        status = 'dead' if robot_manager.dead else 'alive'
        best_fitness = None if robot_manager.best_evaluation is None else robot_manager.best_evaluation.fitness
        log.info(f"status: {status} - Robot fitness: {best_fitness}")
        await asyncio.sleep(5.0)


def main():
    def handler(loop, context):
        exc = context['exception']
        if isinstance(exc, DisconnectError) \
                or isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            sys.exit(0)
        raise context['exception']

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handler)
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Got CtrlC, shutting down.")


if __name__ == '__main__':
    print("STARTING")
    main()
    print("FINISHED")
