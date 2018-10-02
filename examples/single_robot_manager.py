#!/usr/bin/env python2

import os
import sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from pygazebo.pygazebo import DisconnectError
from trollius.py33_exceptions import ConnectionResetError

import trollius
from trollius import From

from revolve.tol.manage import World
from revolve.tol.config import parser

from sdfbuilder import Pose
from sdfbuilder.math import Vector3

from revolve.convert.yaml import yaml_to_robot
from revolve.angle import Tree
from revolve.util import wait_for

from revolve.logging import logger


@trollius.coroutine
def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    conf = parser.parse_args()

    conf.output_directory = "output"
    conf.restore_directory = "restore"
    with open("models/robot_26.yaml", 'r') as yamlfile:
        bot_yaml1 = yamlfile.read()

    with open("models/robot_150.yaml", 'r') as yamlfile:
        bot_yaml2 = yamlfile.read()

    # Create the world, this connects to the Gazebo world

    world = yield From(World.create(conf))

    # These are useful when working with YAML
    body_spec = world.builder.body_builder.spec
    brain_spec = world.builder.brain_builder.spec

    # Create a robot from YAML
    protobot1 = yaml_to_robot(
            body_spec=body_spec,
            nn_spec=brain_spec,
            yaml=bot_yaml1)

    # Create a robot from YAML
    protobot2 = yaml_to_robot(
            body_spec=body_spec,
            nn_spec=brain_spec,
            yaml=bot_yaml2)

    # Create a revolve.angle `Tree` representation from the robot, which
    # is what is used in the world manager.
    robot_tree1 = Tree.from_body_brain(
            body=protobot1.body,
            brain=protobot1.brain,
            body_spec=body_spec)
    # Create a revolve.angle `Tree` representation from the robot, which
    # is what is used in the world manager.
    robot_tree2 = Tree.from_body_brain(
            body=protobot2.body,
            brain=protobot2.brain,
            body_spec=body_spec)
    # Insert the robot into the world. `insert_robot` resolves when the insert
    # request is sent, the future it returns resolves when the robot insert
    # is actually confirmed and a robot manager object has been created
    pose1 = Pose(position=Vector3(0, 0, 0.05))
    pose2 = Pose(position=Vector3(0, 2, 0.05))
    future1 = yield From(world.insert_robot(
            tree=robot_tree1,
            pose=pose1,
            # name="robot_26"
    ))
    future2 = yield From(world.insert_robot(
            tree=robot_tree2,
            pose=pose2,
            # name="robot_26"
    ))
    robot_manager1 = yield From(future1)
    robot_manager2 = yield From(future2)

    # I usually start the world paused, un-pause it here. Note that
    # pause again returns a future for when the request is sent,
    # that future in turn resolves when a response has been received.
    # This is the general convention for all message actions in the
    # world manager. `wait_for` saves the hassle of grabbing the
    # intermediary future in this case.
    yield From(wait_for(world.pause(True)))

    # Start a run loop to do some stuff
    while True:
        # Print robot fitness every second
        print ("Robot fitness is {fitness}".format(
                fitness=robot_manager1.fitness()))
        yield From(trollius.sleep(1.0))


def main():
    def handler(loop, context):
        exc = context['exception']
        if isinstance(exc, DisconnectError) \
                or isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            sys.exit(0)
        raise context['exception']

    try:
        loop = trollius.get_event_loop()
        loop.set_exception_handler(handler)
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Got CtrlC, shutting down.")


if __name__ == '__main__':
    main()
