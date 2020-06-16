from __future__ import absolute_import
from __future__ import division

import numpy as np
from collections import deque

from pyrevolve.SDF.math import Vector3
from pyrevolve.util import Time


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
        self._times = deque(maxlen=speed_window)

        self._positions.append(position)
        self._times.append(time)

        self._dist = 0
        self._time = 0
        self._idx = 0
        self._count = 0

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
