import random as py_random
from pyrevolve.tol.manage import measures
import math
import sys
import numpy as np


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
    if age < (0.25 * robot_manager.conf.evaluation_time) \
            or age < warmup_time:
        # We want at least some data
        return 0.0

    d = 1.0 - (fitness_size_discount * robot_manager.size)
    v = d * (d_fac * measures.displacement_velocity(robot_manager)
             + v_fac * measures.velocity(robot_manager)
             + s_fac * robot_manager.size)
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


def directed_locomotion(robot_manager, robot):
    """
    Fitness is determined by the formula:

    F = e3 * (e1 / (delta + 1) - w * e2)

    Where e1 is the distance travelled in the right direction,
    e2 is the distance of the final position p1 from the ideal
    trajectory starting at starting position p0 and following
    the target direction. e3 rewards locomotion in a straight
    line.
    """

    target_direction_degrees = 0.0  # input in degrees
    weight = 0.01  # default
    ksi = 1.0
    # beta0: float = math.radians(target_direction_degrees)

    path_length = measures.path_length(robot_manager)  # L

    # robot orientation, array[roll, pitch, yaw]
    orient_0 = robot_manager._orientations[0]
    orient_1 = robot_manager._orientations[-1]

    # robot position, Vector3(pos.x, pos.y, pos.z)
    pos_0 = robot_manager._positions[0]
    pos_1 = robot_manager._positions[-1]

    # yaw, basing the target direction on starting orientation (frame of reference) of robot
    # directions(forward) of heads are the orientation(+x axis) - 1.570796
    # Going east: -pi/2.0
    # TODO check logic: test
    beta0 = orient_0[2] - math.pi / 2.0

    # accounts for -pi rad orientation, makes it positive
    if beta0 < - math.pi:
        beta0 = 2 * math.pi - abs(beta0)

    # beta1 = arc tangent of y1 - y0 / x1 - x0 in radians
    beta1 = math.atan2((pos_1[1] - pos_0[1]), (pos_1[0] - pos_0[0]))

    print("Target direction is ", beta0, " radians")
    print("Robot direction is ", beta1, " radians")

    # intersection angle between the target direction and travelled direction
    # always pick smallest angle
    if abs(beta1 - beta0) > math.pi:
        delta = 2 * math.pi - abs(beta1 - beta0)
    else:
        delta = abs(beta1 - beta0)

    # ratio between opposite and adjacent sides; equals 1 in case of beta0 = pi / 2
    A = math.tan(beta0)
    # y0 - A * x0
    B = pos_0[1] - A * pos_0[0]

    X_p = A * (pos_1[1] - B) + pos_1[0] / (A * A + 1)
    Y_p = A * X_p + B

    # calculate the fitness_direction based on dist_projection, alpha, penalty
    if delta > (0.5 * math.pi):
        dist_projection = - math.sqrt((pos_0[0] - X_p) ** 2 + (pos_0[1] - Y_p) ** 2)
    else:
        dist_projection = math.sqrt((pos_0[0] - X_p) ** 2 + (pos_0[1] - Y_p) ** 2)

    dist_penalty = math.sqrt((pos_1[0] - X_p) ** 2 + (pos_1[1] - Y_p) ** 2)
    penalty = 0.01 * dist_penalty

    # fitness = dist_projection / (alpha + ksi) - penalty
    fitness = (abs(dist_projection) / path_length) * (dist_projection / (delta + ksi) - penalty)
    print("Fitness: ", fitness)

    return fitness


def directed_locomotion_test_1(robot_manager, target_direction, weight, robot):
    """
    Fitness is determined by the formula:

    F = e3 * (e1 / (delta + 1) - w * e2)

    Where e1 is the distance travelled in the right direction,
    e2 is the distance of the final position p1 from the ideal
    trajectory starting at starting position p0 and following
    the target direction. e3 rewards locomotion in a straight
    line.
    """

    target_direction = 0.0      # default
    weight = 0.01               # default

    distance, time = measures.displacement(robot_manager)
    dist = distance[0]

    # starting_position = measures.logs_position_orientation(robot_manager, )            # p0(x0, y0)
    # final_position =                # p1(x1, y1)
    # distance_travelled = final_position - starting_position

    rot = robot_manager._orientations[-1]       # roll / pitch / yaw
    angle_degrees = rot[2] * (180 / math.pi)

    deviation_angle = target_direction - angle_degrees                # delta
    length_trajectory = measures.path_length(robot_manager)            # L

    import mpmath
    cotangent: float = mpmath.cot(deviation_angle)
    tangent: float = math.tan(deviation_angle)

    epsilon: float = sys.float_info.epsilon

    e1 = dist * cotangent
    e2 = dist * tangent
    e3 = dist / (length_trajectory + epsilon)
        # approaches but never equals 1 due to epsilon in denominator

    fitness = e3 * (e1 / (deviation_angle + 1) - weight * e2)

    return fitness


def directed_locomotion_test_2(robot_manager, robot):
    """
    Fitness is determined by the formula:

    F = e3 * (e1 / (delta + 1) - w * e2)

    Where e1 is the distance travelled in the right direction,
    e2 is the distance of the final position p1 from the ideal
    trajectory starting at starting position p0 and following
    the target direction. e3 rewards locomotion in a straight
    line.
    """

    target_direction = 0.0      # default
    weight = 0.01               # default

    distance, time = measures.displacement(robot_manager)
    dist = math.sqrt(distance[0] ** 2 + distance[1] ** 2)

    # starting_position = measures.logs_position_orientation(robot_manager, )            # p0(x0, y0)
    # final_position =                # p1(x1, y1)
    # distance_travelled = final_position - starting_position

    rot_i = target_direction
    rot_i_1 = robot_manager._orientations[-1]

    angle_i: float = rot_i  # roll / pitch / yaw
    angle_i_1: float = rot_i_1[2]  # roll / pitch / yaw
    pi_2: float = math.pi / 2.0

    if angle_i_1 > pi_2 and angle_i < - pi_2:  # rotating left
        delta_orientations = 2.0 * math.pi + angle_i - angle_i_1
    elif (angle_i_1 < - pi_2) and (angle_i > pi_2):
        delta_orientations = - (2.0 * math.pi - angle_i + angle_i_1)
    else:
        delta_orientations = angle_i - angle_i_1

    deviation_angle = math.degrees(delta_orientations)             # delta
    length_trajectory = measures.path_length(robot_manager)            # L

    import mpmath
    cotangent: float = mpmath.cot(deviation_angle)
    tangent: float = math.tan(deviation_angle)

    epsilon: float = sys.float_info.epsilon

    e1 = dist * cotangent
    e2 = dist * tangent
    e3 = dist / (length_trajectory + epsilon)
    # approaches but never equals 1 due to epsilon in denominator

    fitness = e3 * (e1 / (deviation_angle + 1) - weight * e2)

    return fitness


def directed_locomotion_test_3(robot_manager, robot):
    """
    Fitness is determined by the formula:

    F = e3 * (e1 / (delta + 1) - w * e2)

    Where e1 is the distance travelled in the right direction,
    e2 is the distance of the final position p1 from the ideal
    trajectory starting at starting position p0 and following
    the target direction. e3 rewards locomotion in a straight
    line.
    """

    target_direction_degrees = 0.0  # input in degrees
    weight = 0.01  # default

    distance, time = measures.displacement(robot_manager)
    dist = math.sqrt(distance[0] ** 2 + distance[1] ** 2)
    target_direction = math.radians(target_direction_degrees)

    # starting_position = measures.logs_position_orientation(robot_manager, )            # p0(x0, y0)
    # final_position =                # p1(x1, y1)
    # distance_travelled = final_position - starting_position

    rot = robot_manager._orientations[-1]           # this takes the robot orientation at T_1, array
    robot_angle: float = rot[2]       # roll / pitch / yaw, this takes the yaw orientation at T_1
    print("Robot is oriented at ", robot_angle, " radians")

    deviation_angle = abs(target_direction - robot_angle)    # delta, absolute value due to minimising
    print("Deviation with target is ", deviation_angle, " radians")
    length_trajectory = measures.path_length(robot_manager)  # L
    print("The displacement is ", dist, "and the path length is ", length_trajectory)

    cotangent: float = mpmath.cot(deviation_angle)          # input in radians
    tangent: float = math.tan(deviation_angle)              # input in radians

    epsilon = sys.float_info.epsilon

    e1 = dist * cotangent
    e2 = dist * tangent
    e3 = dist / (length_trajectory + epsilon)
    # approaches but never equals 1 due to epsilon in denominator

    fitness = e3 * (e1 / (deviation_angle + 1) - weight * e2)
    print("Fitness is ", fitness)

    return fitness


def directed_locomotion_test_4(robot_manager, robot):
    """
    Fitness is determined by the formula:

    F = e3 * (e1 / (delta + 1) - w * e2)

    Where e1 is the distance travelled in the right direction,
    e2 is the distance of the final position p1 from the ideal
    trajectory starting at starting position p0 and following
    the target direction. e3 rewards locomotion in a straight
    line.
    """

    target_direction_degrees = 0.0  # input in degrees
    weight = 0.01  # default

    distance, time = measures.displacement(robot_manager)
    dist = math.sqrt(distance[0] ** 2 + distance[1] ** 2)
    target_direction = math.radians(target_direction_degrees)

    # starting_position = measures.logs_position_orientation(robot_manager, )            # p0(x0, y0)
    # final_position =                # p1(x1, y1)
    # distance_travelled = final_position - starting_position

    rot = robot_manager._orientations[-1]           # this takes the robot orientation at T_1, array
    rot = robot_manager._positions[-1]                  # last robot position at T_1, Vector3(pos.x, pos.y, pos.z)
    robot_angle: float = rot[2]       # roll / pitch / yaw, this takes the yaw orientation at T_1
    print("robot_manager._orientations: ", robot_manager._orientations)
    print("robot_manager._positions: ", robot_manager._positions)
    print("Robot is oriented at ", robot_angle, " radians")

    deviation_angle = abs(target_direction - robot_angle)    # delta, absolute value due to minimising
    print("Deviation with target is ", deviation_angle, " radians")
    length_trajectory = measures.path_length(robot_manager)  # L
    print("The displacement is ", dist, "and the path length is ", length_trajectory)

    cotangent: float = mpmath.cot(deviation_angle)          # input in radians
    tangent: float = math.tan(deviation_angle)              # input in radians

    epsilon = sys.float_info.epsilon

    e1 = dist * cotangent
    e2 = dist * tangent
    e3 = dist / (length_trajectory + epsilon)
    # approaches but never equals 1 due to epsilon in denominator

    fitness = e3 * (e1 / (deviation_angle + 1) - weight * e2)
    print("Fitness is ", fitness)

    return fitness


def rotation(robot_manager, _robot, factor_orien_ds: float = 0.0):
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

        if angle_i_1 > pi_2 and angle_i < - pi_2:  # rotating left
            delta_orientations = 2.0 * math.pi + angle_i - angle_i_1
        elif (angle_i_1 < - pi_2) and (angle_i > pi_2):
            delta_orientations = - (2.0 * math.pi - angle_i + angle_i_1)
        else:
            delta_orientations = angle_i - angle_i_1
        orientations += delta_orientations

    fitness_value: float = orientations - factor_orien_ds * robot_manager._dist
    return fitness_value

