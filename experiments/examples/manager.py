#!/usr/bin/env python3
import os
import sys
import asyncio

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
sys.path.append(newpath)

from pygazebo.pygazebo import DisconnectError

from pyrevolve import parser
from pyrevolve.angle import Tree
from pyrevolve.convert.yaml import yaml_to_robot
from pyrevolve.sdfbuilder import Pose
from pyrevolve.sdfbuilder.math import Vector3
from pyrevolve.tol.manage import World, VREPWorld


async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    conf = parser.parse_args()

    conf.output_directory = "output"
    conf.restore_directory = "restore"
    with open("models/robot_26.yaml", 'r') as yamlfile:
        bot_yaml1 = yamlfile.read()

    if conf.vrep:
        world = VREPWorld.create(conf)
        world.pause(False)
        world.pause(True)
    else:
        world = await World.create(conf)

    # These are useful when working with YAML
    body_spec = world.builder.body_builder.spec
    brain_spec = world.builder.brain_builder.spec

    # Create a robot from YAML
    proto_bot = yaml_to_robot(
        body_spec=body_spec,
        nn_spec=brain_spec,
        yaml=bot_yaml1)

    robot_tree = Tree.from_body_brain(
        body=proto_bot.body,
        brain=proto_bot.brain,
        body_spec=body_spec)
    pose = Pose(position=Vector3(0, 0, 0.05))
    # future = await (world.insert_robot(
    #         tree=robot_tree,
    #         pose=pose,
    #         # robot_name="robot_26"
    # ))
    # robot_manager = await future

    world.insert_robot(
        tree=robot_tree,
        pose=pose,
        robot_name="robot_42"
    )

    # await world.pause(False)
    world.pause(False)

    # Start a run loop to do some stuff
    while True:
        # Print robot fitness every second
        #TODO remove because it's not supported by VREP yet
        # print("Robot fitness is {fitness}".format(
        #         fitness=robot_manager.fitness()))
        await asyncio.sleep(10.0)


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
