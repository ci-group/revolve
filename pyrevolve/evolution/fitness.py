from __future__ import annotations
import random as py_random
import math

from pyrevolve.tol.manage import measures

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyrevolve.angle import RobotManager
    from pyrevolve.revolve_bot import RevolveBot
    from pyrevolve.SDF.math import Vector3


def _distance_flat_plane(pos1: Vector3, pos2: Vector3):
    return math.sqrt(
        (pos1.x - pos2.x) ** 2 + (pos1.y - pos2.y) ** 2
    )


def stupid(_robot_manager, robot):
    return 1.0, None


def random(_robot_manager, robot):
    return py_random.random(), None


def displacement(robot_manager, robot):
    displacement_vec = measures.displacement(robot_manager)[0]
    displacement_vec.z = 0
    return displacement_vec.magnitude(), None


def displacement_velocity(robot_manager, robot):
    return measures.displacement_velocity(robot_manager), None


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
    if age < (0.25 * robot_manager.conf.evaluation_time) \
            or age < warmup_time:
        # We want at least some data
        return 0.0

    d = 1.0 - (fitness_size_discount * robot_manager.size)
    v = d * (d_fac * measures.displacement_velocity(robot_manager)
             + v_fac * measures.velocity(robot_manager)
             + s_fac * robot_manager.size)

    fitness = v if v <= fitness_limit else 0.0
    return fitness, None


def displacement_velocity_hill(robot_manager, robot):
    _displacement_velocity_hill = measures.displacement_velocity_hill(robot_manager)
    if _displacement_velocity_hill < 0:
        _displacement_velocity_hill /= 10
    elif _displacement_velocity_hill == 0:
        _displacement_velocity_hill = -0.1
    # temp elif
   # elif _displacement_velocity_hill > 0:
    #    _displacement_velocity_hill *= _displacement_velocity_hill

    return _displacement_velocity_hill, None


def floor_is_lava(robot_manager, robot):
    _displacement_velocity_hill = measures.displacement_velocity_hill(robot_manager)
    _contacts = measures.contacts(robot_manager, robot)

    _contacts = max(_contacts, 0.0001)
    if _displacement_velocity_hill >= 0:
        fitness = _displacement_velocity_hill / _contacts
    else:
        fitness = _displacement_velocity_hill * _contacts

    return fitness, None


def rotation(robot_manager: RobotManager, _robot: RevolveBot, factor_orien_ds: float = 0.0):
    # TODO move to measurements?
    orientations: float = 0.0
    delta_orientations: float = 0.0

    assert len(robot_manager._orientations) == len(robot_manager._positions)

    for i in range(1, len(robot_manager._orientations)):
        # TODO why are we ignoring time here? is it a good thing?

        pos_i_1: Vector3 = robot_manager._positions[i - 1]
        pos_i: Vector3 = robot_manager._positions[i]
        rot_i_1 = robot_manager._orientations[i - 1]
        rot_i = robot_manager._orientations[i]

        angle_i: float = rot_i[2]  # roll / pitch / yaw
        angle_i_1: float = rot_i_1[2]  # roll / pitch / yaw
        pi_2: float = math.pi / 2.0

        if angle_i_1 > pi_2 and angle_i < - pi_2:  # rotating left
            delta_orientations = 2.0 * math.pi + angle_i - angle_i_1
        elif (angle_i_1 < - pi_2) and (angle_i > pi_2):
            delta_orientations = - (2.0 * math.pi - angle_i + angle_i_1)
        else:
            delta_orientations = angle_i - angle_i_1
        orientations += delta_orientations

    fitness_value: float = orientations - factor_orien_ds * robot_manager._dist
    return fitness_value, None


scale_displacement = 1.0 / 0.873453
scale_rotation = 1.0 / 4.281649

# This will not be part of future code, solely for experimental practice
def displacement_with_rotation(_robot_manager, robot):
    global scale_displacement, scale_rotation

    displacement_fitness = displacement(_robot_manager, robot)[0]
    rotation_fitness = rotation(_robot_manager, robot)[0]

    fitness_distribution = 0.75

    scaled_displacement_fitness = fitness_distribution * scale_displacement * displacement_fitness
    scaled_rotation_fitness = (1 - fitness_distribution) * scale_rotation * rotation_fitness
    total_fitness = scaled_displacement_fitness + scaled_rotation_fitness

    return total_fitness, [scaled_displacement_fitness, scaled_rotation_fitness]


# This will not be part of future code, solely for experimental practice
def displacement_and_rotation(_robot_manager, robot):
    global scale_displacement, scale_rotation

    displacement_fitness = displacement(_robot_manager, robot)[0]
    rotation_fitness = rotation(_robot_manager, robot)[0]

    fitness_distribution = 0.5

    scaled_displacement_fitness = fitness_distribution * scale_displacement * displacement_fitness
    scaled_rotation_fitness = (1 - fitness_distribution) * scale_rotation * rotation_fitness
    total_fitness = scaled_displacement_fitness + scaled_rotation_fitness

    return total_fitness, [scaled_displacement_fitness, scaled_rotation_fitness]


# This will not be part of future code, solely for experimental practice
def rotation_with_displacement(_robot_manager, robot):
    global scale_displacement, scale_rotation

    displacement_fitness = displacement(_robot_manager, robot)[0]
    rotation_fitness = rotation(_robot_manager, robot)[0]

    fitness_distribution = 0.25

    scaled_displacement_fitness = fitness_distribution * scale_displacement * displacement_fitness
    scaled_rotation_fitness = (1 - fitness_distribution) * scale_rotation * rotation_fitness
    total_fitness = scaled_displacement_fitness + scaled_rotation_fitness

    return total_fitness, [scaled_displacement_fitness, scaled_rotation_fitness]
