#!/usr/bin/env python3
import os
import sys
import asyncio

import robot
import voxelmesh

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
from pyrevolve.tol.manage import World

async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    conf = parser.parse_args()

    conf.output_directory = "output"
    conf.restore_directory = "restore"

    world = await World.create(conf)
    await world.pause(True)

    sdf_model = """
    <sdf version ='1.5'>
        <model name ='sphere'>
            <pose>1 0 0 0 0 0</pose>
            <link name ='link'>
                <pose>0 0 .5 0 0 0</pose>
                <collision name ='collision'>
                    <geometry>
                        <sphere>
                            <radius>0.5</radius>
                        </sphere>
                    </geometry>
                </collision>
                <visual name ='visual'>
                    <geometry>
                        <sphere>
                            <radius>0.5</radius>
                        </sphere>
                    </geometry>
                </visual>
            </link>
        </model>
    </sdf>"""

    # await world.insert_model(
    #     sdf=sdf_model,
    # )

    example_robot = robot.ARERobot(name="ARE_blob")
    are_robot_sdf = example_robot.sdf()

    voxel_mesh = voxelmesh.VoxelMesh()
    collada_mesh = voxel_mesh.collada()

    print("\nINSERTING ROBOT SDF\n\n{}\n\n".format(are_robot_sdf))
    await world.insert_model(
        sdf=are_robot_sdf
    )

    await world.pause(False)

    while True:
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
