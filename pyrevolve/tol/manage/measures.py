import numpy as np
import math

from pyrevolve.SDF.math import Vector3
from pyrevolve.util import Time
from pyrevolve.angle.manage.robotmanager import RobotManager as RvRobotManager
from pyrevolve.revolve_bot.revolve_bot import RevolveBot


class BehaviouralMeasurements:
    """
        Calculates all the measurements and saves them in one object
    """
    def __init__(self, robot_manager: RvRobotManager = None, robot: RevolveBot = None):
        """
        :param robot_manager: Revolve Manager that holds the life of the robot
        :param robot: Revolve Bot for measurements relative to the robot morphology and brain
        :type robot: RevolveBot
        """
        if robot_manager is not None and robot is not None:
            self.velocity = velocity(robot_manager)
            self.displacement = displacement(robot_manager)
            self.displacement_velocity = displacement_velocity(robot_manager)
            self.displacement_velocity_hill = displacement_velocity_hill(robot_manager)
            self.head_balance = head_balance(robot_manager)
            self.contacts = contacts(robot_manager, robot)
        else:
            self.velocity = None
            self.displacement = None
            self.displacement_velocity = None
            self.displacement_velocity_hill = None
            self.head_balance = None
            self.contacts = None

    def items(self):
        return {
            'velocity': self.velocity,
            #'displacement': self.displacement,
            'displacement_velocity': self.displacement_velocity,
            'displacement_velocity_hill': self.displacement_velocity_hill,
            'head_balance': self.head_balance,
            'contacts': self.contacts
        }.items()



def velocity(robot_manager: RvRobotManager):
    """
    Returns the velocity over the maintained window
    :return:
    """
    return robot_manager._dist / robot_manager._time if robot_manager._time > 0 else 0


def displacement(robot_manager: RvRobotManager):
    """
    Returns a tuple of the displacement in both time and space
    between the first and last registered element in the speed
    window.
    :return: Tuple where the first item is a displacement vector
             and the second a `Time` instance.
    :rtype: tuple(Vector3, Time)
    """
    if len(robot_manager._positions) == 0:
        return Vector3(0, 0, 0), Time()
    return (
        robot_manager._positions[-1] - robot_manager._positions[0],
        robot_manager._times[-1] - robot_manager._times[0]
    )


def path_length(robot_manager: RvRobotManager):
    return robot_manager._dist


def displacement_velocity(robot_manager: RvRobotManager):
    """
    Returns the displacement velocity, i.e. the velocity
    between the first and last recorded position of the
    robot in the speed window over a straight line,
    ignoring the path that was taken.
    :return:
    """
    dist, time = displacement(robot_manager)
    if time.is_zero():
        return 0.0
    return np.sqrt(dist.x ** 2 + dist.y ** 2) / float(time)


def displacement_velocity_hill(robot_manager: RvRobotManager):
    dist, time = displacement(robot_manager)
    if time.is_zero():
        return 0.0
    return dist.y / float(time)


def head_balance(robot_manager: RvRobotManager):
    """
    Returns the average rotation of teh head in the roll and pitch dimensions.
    :return:
    """
    roll = 0
    pitch = 0
    instants = len(robot_manager._orientations)
    for o in robot_manager._orientations:
        roll = roll + abs(o[0]) * 180 / math.pi
        pitch = pitch + abs(o[1]) * 180 / math.pi
    #  accumulated angles for each type of rotation
    #  divided by iterations * maximum angle * each type of rotation
    if instants == 0:
        balance = None
    else:
        balance = (roll + pitch) / (instants * 180 * 2)
        # turns imbalance to balance
        balance = 1 - balance
    return balance


def contacts(robot_manager: RvRobotManager, robot: RevolveBot):
    """
    Measures the average number of contacts with the floor relative to the body size

    WARN: this measurement could be faulty, several robots were
    found to have 0 contacts if simulation is too fast

    :param robot_manager: reference to the robot in simulation
    :param robot: reference to the robot for size measurement
    :return: average number of contacts per block in the lifetime
    """
    avg_contacts = 0
    for c in robot_manager._contacts:
        avg_contacts += c
    #TODO remove this IF, it's ugly as hell
    if robot._morphological_measurements is None:
        robot._morphological_measurements = robot.measure_body()
    avg_contacts = avg_contacts / robot._morphological_measurements.absolute_size
    return avg_contacts


def logs_position_orientation(robot_manager: RvRobotManager, o, evaluation_time, robotid, path):
    with open(path + '/data_fullevolution/descriptors/positions_' + robotid + '.txt', "a+") as f:
        if robot_manager.second <= evaluation_time:
            robot_manager.avg_roll += robot_manager._orientations[o][0]
            robot_manager.avg_pitch += robot_manager._orientations[o][1]
            robot_manager.avg_yaw += robot_manager._orientations[o][2]
            robot_manager.avg_x += robot_manager._positions[o].x
            robot_manager.avg_y += robot_manager._positions[o].y
            robot_manager.avg_z += robot_manager._positions[o].z
            robot_manager.avg_roll = robot_manager.avg_roll / robot_manager.count_group
            robot_manager.avg_pitch = robot_manager.avg_pitch / robot_manager.count_group
            robot_manager.avg_yaw = robot_manager.avg_yaw / robot_manager.count_group
            robot_manager.avg_x = robot_manager.avg_x / robot_manager.count_group
            robot_manager.avg_y = robot_manager.avg_y / robot_manager.count_group
            robot_manager.avg_z = robot_manager.avg_z / robot_manager.count_group
            robot_manager.avg_roll = robot_manager.avg_roll * 180 / math.pi
            robot_manager.avg_pitch = robot_manager.avg_pitch * 180 / math.pi
            robot_manager.avg_yaw = robot_manager.avg_yaw * 180 / math.pi
            f.write(str(robot_manager.second) + ' '
                    + str(robot_manager.avg_roll) + ' '
                    + str(robot_manager.avg_pitch) + ' '
                    + str(robot_manager.avg_yaw) + ' '
                    + str(robot_manager.avg_x) + ' '
                    + str(robot_manager.avg_y) + ' '
                    + str(robot_manager.avg_z) + '\n')
            robot_manager.second += 1
            robot_manager.avg_roll = 0
            robot_manager.avg_pitch = 0
            robot_manager.avg_yaw = 0
            robot_manager.avg_x = 0
            robot_manager.avg_y = 0
            robot_manager.avg_z = 0
            robot_manager.count_group = 1
