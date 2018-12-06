"""
Generates a bot using the code in `generated_sdf`,
and sends it to the body analyzer to have it analyzed.

If the analysis is accepted, it outputs the bot, otherwise
it generates a new one. Writes the final bot's contents to
stdout, statistics are written to stderr.
"""
from __future__ import absolute_import
from __future__ import print_function

import sys
import random

from sdfbuilder.math import Vector3
from .generated_sdf import generate_robot, builder, robot_to_sdf
from ..gazebo import connect, get_analysis_robot, BodyAnalyzer

import asyncio


if len(sys.argv) > 1:
    seed = int(sys.argv[1])
else:
    seed = random.randint(0, 10000)

random.seed(seed)
print("Seed: {}".format(seed), file=sys.stderr)


async def analysis_func():
    analyzer = await (BodyAnalyzer.create(address=("127.0.0.1", 11346)))

    # Try a maximum of 100 times
    for i in range(100):
        # Generate a new robot
        robot = generate_robot()

        sdf = get_analysis_robot(robot, builder)

        # Find out its intersections and bounding box
        intersections, bbox = await (
                analyzer.analyze_robot(robot, builder=builder))

        if intersections:
            print("Invalid model - intersections detected.", file=sys.stderr)
        else:
            print("No model intersections detected!", file=sys.stderr)
            if bbox:
                # Translate the model in z direction so it stands directly on
                # the ground
                print("Model bounding box: ({}, {}, {}), ({}, {}, {})".format(
                        bbox.min.x,
                        bbox.min.y,
                        bbox.min.z,
                        bbox.max.x,
                        bbox.max.y,
                        bbox.max.z
                ), file=sys.stderr)
                model = sdf.elements[0]
                model.translate(Vector3(0, 0, -bbox.min.z))

            print(str(robot_to_sdf(robot, "test_bot", "controllerplugin.so")))
            break

loop = asyncio.get_event_loop()
loop.run_until_complete(analysis_func())
