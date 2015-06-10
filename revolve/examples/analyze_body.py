"""
Generates a bot using the code in `generated_sdf`,
and sends it to the body analyzer to have it analyzed.

If the analysis is accepted, it outputs the bot, otherwise
it generates a new one. Writes the final bot's contents to
stdout, statistics are written to stderr.
"""
from __future__ import print_function
import sys
from sdfbuilder.math import Vector3
from .generated_sdf import generate_robot, builder, robot_to_sdf
from ..gazebo import analysis_coroutine, connect, get_analysis_robot
import random

import trollius
from trollius import From

if len(sys.argv) > 1:
    seed = int(sys.argv[1])
else:
    seed = random.randint(0, 10000)

random.seed(seed)
print("Seed: %d" % seed, file=sys.stderr)

@trollius.coroutine
def analysis_func():
    manager = yield From(connect(("127.0.0.1", 11346)))

    # Try a maximum of 100 times
    for i in range(100):
        # Generate a new robot
        robot = generate_robot()
        sdf = get_analysis_robot(robot, builder)

        # Find out its intersections and bounding box
        intersections, bbox = yield From(analysis_coroutine(sdf, manager))

        if intersections:
            print("Invalid model - intersections detected.", file=sys.stderr)
        else:
            print("No model intersections detected!", file=sys.stderr)
            if bbox:
                # Translate the model in z direction so it won't land
                # "in" the ground.
                # TODO Bounding box of body analyzer is incorrect, so we add a little space
                # I cannot fully solve that by myself so will have to report
                print("Model bounding box: (%f, %f, %f)" % bbox, file=sys.stderr)
                model = sdf.elements[0]
                model.translate(Vector3(0, 0, 0.5 * bbox[2] + 1))

            print(str(robot_to_sdf(robot, "test_bot", "controllerplugin.so")))
            break

loop = trollius.get_event_loop()
loop.run_until_complete(analysis_func())
