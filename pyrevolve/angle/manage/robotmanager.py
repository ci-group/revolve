from __future__ import absolute_import
from __future__ import division

import numpy as np
from collections import deque

from pyrevolve.SDF.math import Vector3, Quaternion
from pyrevolve.util import Time
import math
import os

class RobotManager(object):
    """
    Class to manage a single robot with the WorldManager
    """

    def __init__(
            self,
            robot,
            position,
            time,
            battery_level=0.0,
            speed_window=60,
            warmup_time=0,
    ):
        """
        :param speed_window:
        :param robot: RevolveBot
        :param position:
        :type position: Vector3
        :param time:
        :type time: Time
        :param battery_level:
        :type battery_level: float
        :return:
        """
        self.warmup_time = warmup_time
        self.speed_window = speed_window
        self.robot = robot
        self.starting_position = position
        self.starting_time = time
        self.battery_level = battery_level

        self.last_position = position
        self.last_update = time
        self.last_mate = None

        self._ds = deque(maxlen=speed_window)
        self._dt = deque(maxlen=speed_window)
        self._positions = deque(maxlen=speed_window)
        self._orientations = deque(maxlen=speed_window)
        self._contacts = deque(maxlen=speed_window)
        self._seconds = deque(maxlen=speed_window)
        self._times = deque(maxlen=speed_window)

        self._dist = 0
        self._time = 0
        self._idx = 0
        self._count = 0
        self.second = 1
        self.count_group = 1
        self.avg_roll = 0
        self.avg_pitch = 0
        self.avg_yaw = 0
        self.avg_x = 0
        self.avg_y = 0
        self.avg_z = 0

    @property
    def name(self):
        return str(self.robot.id)

    def update_state(self, world, time, state, poses_file):
        """
        Updates the robot state from a state message.

        :param world: Instance of the world
        :param time: The simulation time at the time of this
                     position update.
        :type time: Time
        :param state: State message
        :param poses_file: CSV writer to write pose to, if applicable
        :type poses_file: csv.writer
        :return:
        """
        pos = state.pose.position
        position = Vector3(pos.x, pos.y, pos.z)

        rot = state.pose.orientation
        qua = Quaternion(rot.w, rot.x, rot.y, rot.z)
        euler = qua.get_rpy()
        euler = np.array([euler[0], euler[1], euler[2]]) # roll / pitch / yaw

        age = world.age()

        if self.starting_time is None:
            self.starting_time = time
            self.last_update = time
            self.last_position = position

        if poses_file:
            age = world.age()
            poses_file.writerow([self.robot.id, age.sec, age.nsec,
                                 position.x, position.y, position.z,
                                 self.get_battery_level()])

        if float(self.age()) < self.warmup_time:
            # Don't update position values within the warmup time
            self.last_position = position
            self.last_update = time
            return

        # Calculate the distance the robot has covered as the Euclidean
        # distance over the x and y coordinates (we don't care for flying),
        # as well as the time it took to cover this distance.
        last = self.last_position
        ds = np.sqrt((position.x - last.x)**2 + (position.y - last.y)**2)
        dt = float(time - self.last_update)

        # Velocity is of course sum(distance) / sum(time)
        # Storing all separate distance and time values allows us to
        # efficiently calculate the new speed over the window without
        # having to sum the entire arrays each time, by subtracting
        # the values we're about to remove from the _dist / _time values.
        self._dist += ds
        self._time += dt

        if len(self._dt) >= self.speed_window:
            # Subtract oldest values if we're about to override it
            self._dist -= self._ds[-1]
            self._time -= self._dt[-1]

        self.last_position = position
        self.last_update = time

        self._positions.append(position)
        self._times.append(time)
        self._ds.append(ds)
        self._dt.append(dt)
        self._orientations.append(euler)
        self._seconds.append(age.sec)

    def update_contacts(self, world, module_contacts):

        number_contacts = 0
        for position in module_contacts.position:
            number_contacts += 1

        self._contacts.append(number_contacts)

    def sum_of_contacts(self):
        sum_of_contacts = 0
        for c in self._contacts:
            sum_of_contacts += c
        return sum_of_contacts

    def age(self):
        """
        Returns this robot's age as a Time object.
        Depends on the last and first update times.
        :return:
        :rtype: Time
        """
        return Time() \
            if self.last_update is None \
            else self.last_update - self.starting_time

    def get_battery_level(self):
        """
        Method to return the robot battery level. How the battery level
        is managed is probably implementation specific, so you'll likely
        have to modify this method for your specific use.
        :return:
        """
        return self.battery_level

    ## init behavioral measures
    # we should move it to a file only with behavioral measures !!!! maybe revolve bot???

    def velocity(self):
        """
        Returns the velocity over the maintained window
        :return:
        """
        return self._dist / self._time if self._time > 0 else 0

    def displacement(self):
        """
        Returns a tuple of the displacement in both time and space
        between the first and last registered element in the speed
        window.
        :return: Tuple where the first item is a displacement vector
                 and the second a `Time` instance.
        :rtype: tuple(Vector3, Time)
        """
        if self.last_position is None:
            return Vector3(0, 0, 0), Time()

        return (
            self._positions[-1] - self._positions[0],
            self._times[-1] - self._times[0]
        )

    def displacement_velocity(self):
        """
        Returns the displacement velocity, i.e. the velocity
        between the first and last recorded position of the
        robot in the speed window over a straight line,
        ignoring the path that was taken.
        :return:
        """
        dist, time = self.displacement()
        if time.is_zero():
            return 0.0

        return np.sqrt(dist.x**2 + dist.y**2) / float(time)

    def displacement_velocity_hill(self):

        dist, time = self.displacement()
        if time.is_zero():
            return 0.0

        return dist.y / float(time)

    def head_balance(self):
        """
        Returns the average rotation of teh head in the roll and pitch dimensions.
        :return:
        """
        roll = 0
        pitch = 0

        instants = len(self._orientations)

        for o in self._orientations:

            roll = roll + abs(o[0]) * 180 / math.pi
            pitch = pitch + abs(o[1]) * 180 / math.pi

        #  accumulated angles for each type of rotation
        #  divided by iterations * maximum angle * each type of rotation
        balance = (roll + pitch) / (instants * 180 * 2)

        # turns imbalance to balance
        balance = 1 - balance

        return balance

    def logs_position_orientation(self, o, evaluation_time, robotid, generation, experiment_name):
        # define a path properly somewhere!!!!!!
        f = open('../../../l-system/experiments/'+ experiment_name+'/offspringpop'+generation+'/positions_'+robotid+'.txt', "a+")

        if self.second <= evaluation_time:

            self.avg_roll += self._orientations[o][0]
            self.avg_pitch += self._orientations[o][1]
            self.avg_yaw += self._orientations[o][2]
            self.avg_x += self._positions[o].x
            self.avg_y += self._positions[o].y
            self.avg_z += self._positions[o].z

            self.avg_roll = self.avg_roll/self.count_group
            self.avg_pitch = self.avg_pitch/self.count_group
            self.avg_yaw = self.avg_yaw/self.count_group
            self.avg_x = self.avg_x/self.count_group
            self.avg_y = self.avg_y/self.count_group
            self.avg_z = self.avg_z/self.count_group

            self.avg_roll = self.avg_roll * 180 / math.pi

            self.avg_pitch = self.avg_pitch * 180 / math.pi

            self.avg_yaw = self.avg_yaw * 180 / math.pi

            f.write(str(self.second) + ' ' + str(self.avg_roll) + ' ' + str(self.avg_pitch) + ' ' + str(self.avg_yaw)
                    + ' ' + str(self.avg_x) + ' ' + str(self.avg_y) + ' ' + str(self.avg_z) + '\n')

            self.second += 1
            self.avg_roll = 0
            self.avg_pitch = 0
            self.avg_yaw = 0
            self.avg_x = 0
            self.avg_y = 0
            self.avg_z = 0
            self.count_group = 1
        f.close()

    ## end behavioral measures !!!! move !!!!


    ## init fitness functions
    # we should move it to a file only with behavioral measures !!!!

    def fitness_displacement_velocity(self):
        return self.displacement_velocity()

    def fitness_displacement_velocity_hill(self):
        displacement_velocity_hill = self.displacement_velocity_hill()
        if displacement_velocity_hill < 0:
            displacement_velocity_hill /= 10
        elif displacement_velocity_hill == 0:
            displacement_velocity_hill = -0.1
        #elif displacement_velocity_hill > 0:
        #displacement_velocity_hill *= displacement_velocity_hill
        return displacement_velocity_hill


    ## end fitness functions !!!! move !!!!