#!/usr/bin/env python3
import os
import sys
import asyncio

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
sys.path.append(newpath)

from pygazebo.pygazebo import DisconnectError

from pyrevolve import revolve_bot
from pyrevolve import parser
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import World

from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor


async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    settings = parser.parse_args()

    # Load a robot from yaml
    robot = revolve_bot.RevolveBot()
    if settings.robot_yaml is None:
        robot.load_file("experiments/bo_learner/yaml/spider9.yaml")
    else:
        robot.load_file(settings.robot_yaml)
    robot.update_substrate()


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



    # Connect to the simulator and pause
    world = await World.create(settings, world_address=('localhost', settings.port_start))
    await world.pause(True)

    await world.delete_model(robot.id)
    await asyncio.sleep(2.5)

    # Insert the robot in the simulator
    robot_manager = await world.insert_robot(robot, Vector3(0, 0, 0.025))

    # Resume simulation
    await world.pause(False)

    # Start a run loop to do some stuff
    while True:
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
