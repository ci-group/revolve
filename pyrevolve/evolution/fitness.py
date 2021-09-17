from __future__ import annotations

import math
import random as py_random
import sys
from typing import TYPE_CHECKING, Tuple

from pyrevolve.custom_logging.logger import logger
from pyrevolve.revolve_bot.revolve_module import Orientation
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import measures

if TYPE_CHECKING:
    from pyrevolve.angle import RobotManager
    from pyrevolve.revolve_bot import RevolveBot


def _distance_flat_plane(pos1: Vector3, pos2: Vector3):
    return math.sqrt((pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2)


def stupid(_robot_manager, robot):
    return 1.0


def random(_robot_manager, robot):
    return py_random.random()


def displacement(robot_manager, robot):
    displacement_vec = measures.displacement(robot_manager)[0]
    displacement_vec.z = 0
    return displacement_vec.magnitude()


def displacement_velocity(robot_manager, robot):
    return measures.displacement_velocity(robot_manager)


def online_old_revolve(robot_manager):
    """
    Fitness is proportional to both the displacement and absolute
    velocity of the center of mass of the robot, in the formula:

    (1 - d l) * (a dS + b S + c l)

    Where dS is the displacement over a direct line between the
    start and end points of the robot, S is the distance that
    the robot has moved and l is the robot size.

    Since we use an active speed window, we use this formula
    in context of velocities instead. The parameters a, b and c
    are modifyable through config.
    :return: fitness value
    """
    # these parameters used to be command line parameters
    warmup_time = 0.0
    v_fac = 1.0  # fitness_velocity_factor
    d_fac = 5.0  # fitness_displacement_factor
    s_fac = 0.0  # fitness_size_factor
    fitness_size_discount = 0.0
    fitness_limit = 1.0

    age = robot_manager.age()
    if age < (0.25 * robot_manager.conf.evaluation_time) or age < warmup_time:
        # We want at least some data
        return 0.0

    d = 1.0 - (fitness_size_discount * robot_manager.size)
    v = d * (
        d_fac * measures.displacement_velocity(robot_manager)
        + v_fac * measures.velocity(robot_manager)
        + s_fac * robot_manager.size
    )
    return v if v <= fitness_limit else 0.0


def displacement_velocity_hill(robot_manager, robot):
    _displacement_velocity_hill = measures.displacement_velocity_hill(robot_manager)
    if _displacement_velocity_hill < 0:
        _displacement_velocity_hill /= 10
    elif _displacement_velocity_hill == 0:
        _displacement_velocity_hill = -0.1
    # temp elif
    # elif _displacement_velocity_hill > 0:
    #    _displacement_velocity_hill *= _displacement_velocity_hill

    return _displacement_velocity_hill


def floor_is_lava(robot_manager, robot):
    _displacement_velocity_hill = measures.displacement_velocity_hill(robot_manager)
    _contacts = measures.contacts(robot_manager, robot)

    _contacts = max(_contacts, 0.0001)
    if _displacement_velocity_hill >= 0:
        fitness = _displacement_velocity_hill / _contacts
    else:
        fitness = _displacement_velocity_hill * _contacts

    return fitness


def rotation(
    robot_manager: RobotManager, _robot: RevolveBot, factor_orien_ds: float = 0.0
):
    # TODO move to measurements?
    orientations: float = 0.0
    delta_orientations: float = 0.0

    assert len(robot_manager._orientations) == len(robot_manager._positions)

    for i in range(1, len(robot_manager._orientations)):
        rot_i_1 = robot_manager._orientations[i - 1]
        rot_i = robot_manager._orientations[i]

        angle_i: float = rot_i[2]  # roll / pitch / yaw
        angle_i_1: float = rot_i_1[2]  # roll / pitch / yaw
        pi_2: float = math.pi / 2.0

        if angle_i_1 > pi_2 and angle_i < -pi_2:  # rotating left
            delta_orientations = 2.0 * math.pi + angle_i - angle_i_1
        elif (angle_i_1 < -pi_2) and (angle_i > pi_2):
            delta_orientations = -(2.0 * math.pi - angle_i + angle_i_1)
        else:
            delta_orientations = angle_i - angle_i_1
        orientations += delta_orientations

    fitness_value: float = orientations - factor_orien_ds * robot_manager._dist
    return fitness_value


def panoramic_rotation(
    robot_manager, robot: RevolveBot, vertical_angle_limit: float = math.pi / 4
):
    """
    This fitness evolves robots that take a panoramic scan of their surroundings.
    If the chosen forward vector ever points too much upwards or downwards (limit defined by `vertical_angle_limit`),
    the fitness is reported only up to the point of "failure".

    In this fitness, I'm assuming any "grace time" is not present in the data and the first data points
    in the robot_manager queues are the starting evaluation points.
    :param robot_manager: Behavioural data of the robot
    :param robot: Robot object
    :param vertical_angle_limit: vertical limit that if passed will invalidate any subsequent step of the robot.
    :return: fitness value
    """
    total_angle = 0.0
    vertical_limit = math.sin(vertical_angle_limit)

    # decide which orientation to choose, [0] is correct because the "grace time" values are discarded by the deques
    if len(robot_manager._orientation_vecs) == 0:
        return total_angle

    # Chose orientation base on the
    chosen_orientation = None
    min_z = 1.0
    for orientation, vec in robot_manager._orientation_vecs[0].items():
        z = abs(vec.z)
        if z < min_z:
            chosen_orientation = orientation
            min_z = z
    logger.info(f"Chosen orientation for robot {robot.id} is {chosen_orientation}")

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
        u: Vector3 = vec_list[i - 1]
        v: Vector3 = vec_list[i]

        # if vector is too vertical, fail the fitness
        # (assuming these are unit vectors)
        if abs(u.z) > vertical_limit:
            return total_angle

        dot = u.x * v.x + u.y * v.y  # dot product between [x1, y1] and [x2, y2]
        det = u.x * v.y - u.y * v.x  # determinant
        delta = math.atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)

        total_angle += delta

    return total_angle


def follow_line(robot_manager: RobotManager, robot: RevolveBot) -> float:
    """
    As per Emiel's master's research.

    Fitness is determined by the formula:

    F = e3 * (e1 / (delta + 1) - penalty_factor * e2)

    Where e1 is the distance travelled in the right direction,
    e2 is the distance of the final position p1 from the ideal
    trajectory starting at starting position p0 and following
    the target direction. e3 is distance in right direction divided by
    length of traveled path(curved) + infinitesimal constant to never divide
    by zero.
    delta is angle between optimal direction and traveled direction.
    """
    penalty_factor = 0.01

    epsilon: float = sys.float_info.epsilon

    # length of traveled path(over the complete curve)
    path_length = measures.path_length(robot_manager)  # L

    # robot position, Vector3(pos.x, pos.y, pos.z)
    pos_0 = robot_manager._positions[0]  # start
    pos_1 = robot_manager._positions[-1]  # end

    # robot displacement
    displacement: Tuple[float, float] = (pos_1[0] - pos_0[0], pos_1[1] - pos_0[1])
    displacement_length = math.sqrt(displacement[0] ** 2 + displacement[1] ** 2)
    if displacement_length > 0:
        displacement_normalized = (
            displacement[0] / displacement_length,
            displacement[1] / displacement_length,
        )
    else:
        displacement_normalized = (0, 0)

    # steal target from brain
    # is already normalized
    target = robot._brain.target
    target_length = math.sqrt(target[0] ** 2 + target[1] ** 2)
    target_normalized = (target[0] / target_length, target[1] / target_length)

    # angle between target and actual direction
    delta = math.acos(
        min(  # bound to account for small float errors. acos crashes on 1.0000000001
            1.0,
            max(
                -1,
                target_normalized[0] * displacement_normalized[0]
                + target_normalized[1] * displacement_normalized[1],
            ),
        )
    )

    # projection of displacement on target line
    dist_in_right_direction: float = (
        displacement[0] * target_normalized[0] + displacement[1] * target_normalized[1]
    )

    # distance from displacement to target line
    dist_to_optimal_line: float = math.sqrt(
        (dist_in_right_direction * target_normalized[0] - displacement[0]) ** 2
        + (dist_in_right_direction * target_normalized[1] - displacement[1]) ** 2
    )

    logger.info(
        f"target: {target}, displacement: {displacement}, dist_in_right_direction: {dist_in_right_direction}, dist_to_optimal_line: {dist_to_optimal_line}, delta: {delta}, path_length: {path_length}"
    )

    # filter out passive blocks
    if dist_in_right_direction < 0.01:
        fitness = 0
        logger.info(f"Did not pass fitness test, fitness = {fitness}")
    else:
        fitness = (dist_in_right_direction / (epsilon + path_length)) * (
            dist_in_right_direction / (delta + 1)
            - penalty_factor * dist_to_optimal_line
        )

        logger.info(f"Fitness = {fitness}")

    return fitness
