#!/usr/bin/env python3

import json
import math
import sys
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np

absbase = "/home/aart/projects/revolve/experiments/jlo/data/25th3/1"


def validate(filepath, plot):
    filepath = (
        absbase
        + "/data_fullevolution/descriptors/"
        + "simulation_"
        + filepath
        + ".json"
    )

    with open(filepath, "r") as openfile:
        print("------------------")
        print(f"validation for {filepath}")

        contents = openfile.read()
        log = json.loads(contents)

        print(f"#steps: {len(log['steps'])}")

        positions = [step["position"] for step in log["steps"]]
        target = log["target"]

        path_length = 0
        for i, position in enumerate(positions[:-1]):
            # a = np.array(positions[i - 1])
            # b = np.array(position)
            # path_length += np.linalg.norm(np.subtract(b, a))

            path_length += math.sqrt(
                (positions[i + 1][0] - position[0]) ** 2
                + (positions[i + 1][1] - position[1]) ** 2
            )

        epsilon: float = sys.float_info.epsilon
        penalty_factor = 0.01

        pos_0 = positions[0]
        pos_1 = positions[-1]
        displacement: Tuple[float, float] = (pos_1[0] - pos_0[0], pos_1[1] - pos_0[1])
        displacement_length = math.sqrt(displacement[0] ** 2 + displacement[1] ** 2)
        if displacement_length > 0:
            displacement_normalized = (
                displacement[0] / displacement_length,
                displacement[1] / displacement_length,
            )
        else:
            displacement_normalized = (0, 0)

        target_length = math.sqrt(target[0] ** 2 + target[1] ** 2)
        target_normalized = (target[0] / target_length, target[1] / target_length)

        delta = math.acos(
            min(  # bound to account for small float errors. acos crashes on 1.0000000001
                1.0,
                max(
                    0,
                    target_normalized[0] * displacement_normalized[0]
                    + target_normalized[1] * displacement_normalized[1],
                ),
            )
        )

        # projection of displacement on target line
        dist_in_right_direction: float = (
            displacement[0] * target_normalized[0]
            + displacement[1] * target_normalized[1]
        )

        # distance from displacement to target line
        dist_to_optimal_line: float = math.sqrt(
            (dist_in_right_direction * target_normalized[0] - displacement[0]) ** 2
            + (dist_in_right_direction * target_normalized[1] - displacement[1]) ** 2
        )

        print(
            f"target: {target}, displacement: {displacement}, dist_in_right_direction: {dist_in_right_direction}, dist_to_optimal_line: {dist_to_optimal_line}, delta: {delta}, path_length: {path_length}"
        )

        # filter out passive blocks
        if dist_in_right_direction < 0.01:
            fitness = 0
            print("Did not pass fitness test, fitness = ", fitness)
        else:
            fitness = (dist_in_right_direction / (epsilon + path_length)) * (
                dist_in_right_direction / (delta + 1)
                - penalty_factor * dist_to_optimal_line
            )

            print("Fitness = ", fitness)

        xs = [pos[0] for pos in positions]
        ys = [pos[1] for pos in positions]

        if plot:
            plt.scatter(xs[1:], ys[1:])
            plt.scatter(xs[0], ys[0], color="red", zorder=1000)
            plt.scatter(xs[-1], ys[-1], color="red", zorder=1000)
            plt.scatter(target[0], target[1], color="yellow")
            plt.plot(xs, ys)
            plt.xlabel("x [m]")
            plt.ylabel("y [m]")
            plt.axis("equal")
            plt.grid(True)
            plt.show()


for fullpath in ["2489_iter_1", "2489_iter_2", "2489_iter_3"]:
    validate(fullpath, True)  # fullpath[1])
