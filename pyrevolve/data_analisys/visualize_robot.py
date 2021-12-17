import argparse
import logging
from typing import AnyStr

import math
import numpy as np
import sys

from pyrevolve import parser
from pyrevolve.SDF.math import Vector3
from pyrevolve.custom_logging import logger
from pyrevolve.revolve_bot import RevolveBot


async def test_robot_run(robot_file_path: AnyStr):
    log: logging.Logger = logger.create_logger('experiment', handlers=[
        logging.StreamHandler(sys.stdout),
    ])
    log.setLevel(logging.DEBUG)
    settings: argparse.Namespace = parser.parse_args()

    if settings.simulator_cmd == 'gazebo' or settings.simulator_cmd == 'gzserver':
        from pyrevolve.data_analisys.visualize_robot_gazebo import test_robot_run_gazebo
        return await test_robot_run_gazebo(robot_file_path, log, settings)
    elif settings.simulator_cmd == 'isaac':
        from pyrevolve.data_analisys.visualize_robot_isaac import test_robot_run_isaac
        return test_robot_run_isaac(robot_file_path, log, settings)
    else:
        log.fatal(f"Simulator {settings.simulator_cmd} not recognized! exiting now.")


def rotation(robot_manager, _robot, factor_orien_ds: float = 0.0):
    # TODO move to measurements?
    orientations: float = 0.0
    delta_orientations: float = 0.0

    assert len(robot_manager._orientations) == len(robot_manager._positions)

    fitnesses = [0.]
    choices = ['None']
    i = 0

    for i in range(1, len(robot_manager._orientations)):
        rot_i_1 = robot_manager._orientations[i - 1]
        rot_i = robot_manager._orientations[i]

        angle_i: float = rot_i[2]  # roll / pitch / yaw
        angle_i_1: float = rot_i_1[2]  # roll / pitch / yaw
        pi_2: float = math.pi / 2.0

        if angle_i_1 > pi_2 and angle_i < - pi_2:  # rotating left
            choice = 'A'
            delta_orientations = (2.0 * math.pi + angle_i - angle_i_1) #% (math.pi * 2.0)
        elif (angle_i_1 < - pi_2) and (angle_i > pi_2):
            choice = 'B'
            delta_orientations = - (2.0 * math.pi - angle_i + angle_i_1) #% (math.pi * 2.0)
        else:
            choice = 'C'
            delta_orientations = angle_i - angle_i_1
        #print(f"{choice} {i}\t{delta_orientations:2.0f}\t= {angle_i:2.0f} - {angle_i_1:2.0f}")
        i += 1
        orientations += delta_orientations
        fitnesses.append(orientations)
        choices.append(choice)

    fitnesses = np.array(fitnesses)
    fitnesses -= factor_orien_ds * robot_manager._dist
    return (fitnesses, choices)


def panoramic_rotation(robot_manager, robot: RevolveBot, vertical_angle_limit: float = math.pi/4):
    total_angle = 0.0
    total_angles = [0.]
    vertical_limit = math.sin(vertical_angle_limit)

    # decide which orientation to choose, [0] is correct because the "grace time" values are discarded by the deques
    if len(robot_manager._orientation_vecs) == 0:
        return total_angles

    # Chose orientation base on the
    chosen_orientation = None
    min_z = 1.0
    for orientation, vec in robot_manager._orientation_vecs[0].items():
        z = abs(vec.z)
        if z < min_z:
            chosen_orientation = orientation
            min_z = z
    print(f"Chosen orientation for robot {robot.id} is {chosen_orientation}")

    vec_list = [vecs[chosen_orientation] for vecs in robot_manager._orientation_vecs]

    for i in range(1, len(robot_manager._orientation_vecs)):
        # from: https://code-examples.net/en/q/d6a4f5
        # more info: https://en.wikipedia.org/wiki/Atan2
        # Just like the dot product is proportional to the cosine of the angle,
        # the determinant is proportional to its sine. So you can compute the angle like this:
        #
        # dot = x1*x2 + y1*y2      # dot product between [x1, y1] and [x2, y2]
        # det = x1*y2 - y1*x2      # determinant
        # angle = atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)
        #
        # The function atan2(y,x) (from "2-argument arctangent") is defined as the angle in the Euclidean plane,
        # given in radians, between the positive x axis and the ray to the point (x, y) ≠ (0, 0).

        # u = prev vector
        # v = curr vector
        u: Vector3 = vec_list[i-1]
        v: Vector3 = vec_list[i]

        # if vector is too vertical, fail the fitness
        # (assuming these are unit vectors)
        if abs(u.z) > vertical_limit:
            while len(total_angles) < len(robot_manager._orientations):
                total_angles.append(total_angles[-1])
            return total_angles

        dot = u.x*v.x + u.y*v.y       # dot product between [x1, y1] and [x2, y2]
        det = u.x*v.y - u.y*v.x       # determinant
        delta = math.atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)

        total_angle += delta
        total_angles.append(total_angle)

    return total_angles