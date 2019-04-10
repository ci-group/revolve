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


async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    settings = parser.parse_args()

    # Load a robot from yaml
    robot = revolve_bot.RevolveBot()
    robot.load_file("yaml/spider.yaml")
    robot.update_substrate()

    # Connect to the simulator and pause
    world = await World.create(settings)
    await world.pause(True)

    await (await world.delete_model(robot.id))
    await asyncio.sleep(2.5)

    # Insert the robot in the simulator
    insert_future = await world.insert_robot(robot, Vector3(0, 0, 0.25))
    robot_manager = await insert_future

    # Resume simulation
    await world.pause(False)

    # Start a run loop to do some stuff
    while True:
        # Print robot fitness every second
        print("Robot fitness is {fitness}".format(
                fitness=robot_manager.fitness()))
        await asyncio.sleep(1.0)


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
