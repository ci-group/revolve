"""
Generates a bot using the code in `generated_sdf`,
and sends it to the body analyzer to have it analyzed.

If the analysis is accepted, it outputs the bot, otherwise
it generates a new one. Writes the final bot's contents to
stdout, statistics are written to stderr.
"""
from __future__ import absolute_import, print_function

import asyncio
import random
import sys

from pyrevolve.sdfbuilder.math import Vector3

from ..custom_logging.logger import logger
from ..gazebo import BodyAnalyzer, get_analysis_robot
from .generated_sdf import builder, generate_robot, robot_to_sdf


async def analysis_func():
    analyzer = await (BodyAnalyzer.create(address=("127.0.0.1", 11346)))

    # Try a maximum of 100 times
    for _ in range(100):
        # Generate a new robot
        robot = generate_robot()

        sdf = get_analysis_robot(robot, builder)

        # Find out its intersections and bounding box
        intersections, bbox = await (analyzer.analyze_robot(robot, builder=builder))

        if intersections:
            logger.info("Invalid model - intersections detected.", file=sys.stderr)
        else:
            logger.info("No model intersections detected!", file=sys.stderr)
            if bbox:
                # Translate the model in z direction so it stands directly on
                # the ground
                logger.info(
                    "Model bounding box: ({}, {}, {}), ({}, {}, {})".format(
                        bbox.min.x,
                        bbox.min.y,
                        bbox.min.z,
                        bbox.max.x,
                        bbox.max.y,
                        bbox.max.z,
                    ),
                    file=sys.stderr,
                )
                model = sdf.elements[0]
                model.translate(Vector3(0, 0, -bbox.min.z))

            logger.info(str(robot_to_sdf(robot, "test_bot", "controllerplugin.so")))
            break


loop = asyncio.get_event_loop()
loop.run_until_complete(analysis_func())
