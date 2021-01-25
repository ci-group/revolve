from __future__ import absolute_import
from __future__ import division

import numpy as np
from pyrevolve.SDF.math import Vector3, Quaternion
import math

from pyrevolve.angle import RobotManager as RvRobotManager
from pyrevolve.util import Time

from pyrevolve.tol.manage import measures as ms
from pyrevolve.evolution import fitness


class RobotManager(RvRobotManager):
    """
    Class to manage a single robot
    """

    def __init__(
            self,
            conf,
            robot,
            position,
            time,
            battery_level=0.0,
            position_log_size=None,
            warmup_time=0.0,
    ):
        """
        :param conf:
        :param robot: RevolveBot
        :param position:
        :type position: Vector3
        :param time:
        :type time: Time
        :param battery_level: Battery charge for this robot
        :type battery_level: float
        :return:
        """
        time = conf.evaluation_time if time is None else time
        speed_window = int(float(time) * conf.pose_update_frequency) + 1 if position_log_size is None \
            else position_log_size
        super(RobotManager, self).__init__(
                robot=robot,
                position=position,
                time=time,
                battery_level=battery_level,
                speed_window=speed_window,
                warmup_time=warmup_time,
        )

        # Set of robots this bot has mated with
        self.mated_with = {}
        self.last_mate = None
        self.conf = conf
        self.size = robot.size()
        self.battery_level = battery_level
        self.initial_charge = battery_level

    def update_from_celery(self, msg, world):
        """Celery messages are json and not robot manager. This function is called by
        the celery converter function msg_to_robotmanager() inside the converter.py.
        :param msg: a celery result message"""

        self.dead = True # if we are here robot is already done.

        if self.starting_time is None:
            self.starting_time = msg["times"][0]
            self.last_update = msg["times"][0]
            self.last_position = Vector3(msg["x"][0],msg["y"][0],msg["z"][0])

        # update states
        for i in range(len(msg["x"])):
            position = Vector3(msg["x"][i],msg["y"][i],msg["z"][i])
            euler = np.array([msg["roll"][i],msg["pitch"][i], msg["yaw"][i]])

            # Please note that age is currently corrupted. Because the robot might not have been
            # simulated in the world created by this thread! TO DO: Change age, get it somehow or delete it.
            age = world.age()

            last = self.last_position
            ds = ds = np.sqrt((position.x - last.x)**2 + (position.y - last.y)**2)
            dt = float(msg["times"][i] - self.last_update)

            self._dist += ds
            self._time += dt

            if len(self._dt) >= self.speed_window:
                # Subtract oldest values if we're about to override it
                self._dist -= self._ds[-1]
                self._time -= self._dt[-1]

            self.last_position = position
            self.last_update = msg["times"][i]

            self._positions.append(position)
            self._times.append(msg["times"][i])
            self._ds.append(ds)
            self._dt.append(dt)
            self._orientations.append(euler)
            self._seconds.append(age.sec)

        # update contacts
        self._contacts = msg["contacts"]

    def will_mate_with(self, other):
        """
        Decides whether or not to mate with the other given robot based on
        its position and speed.
        :param other:
        :type other: RobotManager
        :return:
        """
        if self.age() < self.warmup_time:
            # Don't mate within the warmup time
            return False

        mate_count = self.mated_with.get(other.name, 0)
        if mate_count > self.conf.max_pair_children:
            # Maximum number of children with this other parent
            # has been reached
            return False

        if self.last_mate is not None and \
                float(self.last_update - self.last_mate) < \
                self.conf.gestation_period:
            # Don't mate within the cooldown window
            return False

        if self.distance_to(other.last_position) > \
                self.conf.mating_distance_threshold:
            return False

        my_fitness = self.old_revolve_fitness()
        other_fitness = other.old_revolve_fitness()

        # Only mate with robots with nonzero fitness, check for self
        # zero-fitness to prevent division by zero.
        return other_fitness > 0 and (
            my_fitness == 0 or
            (other_fitness / my_fitness) >= self.conf.mating_fitness_threshold
        )

    @staticmethod
    def header():
        """
        :return:
        """
        return [
            'run', 'id', 't_birth',
            'parent1', 'parent2', 'nparts',
            'x', 'y', 'z',
            'extremity_count', 'joint_count', 'motor_count',
            'inputs', 'outputs', 'hidden', 'conn'
        ]

    # def write_robot(self, world, details_file, csv_writer):
    #     """
    #     :param world:
    #     :param details_file:
    #     :param csv_writer:
    #     :return:
    #     """
    #     with open(details_file, 'w') as f:
    #         f.write(self.robot.SerializeToString())
    #
    #     row = [getattr(world, 'current_run', 0), self.robot.id,
    #            world.age()]
    #     row += list(self.parent_ids) if self.parent_ids else ['', '']
    #     row += [self.size, self.last_position.x,
    #             self.last_position.y, self.last_position.z]
    #
    #     root = self.tree.root
    #     inputs, outputs, hidden = root.io_count(recursive=True)
    #     row += [
    #         count_extremities(root),
    #         count_joints(root),
    #         count_motors(root),
    #         inputs,
    #         outputs,
    #         hidden,
    #         count_connections(root)
    #     ]
    #
    #     csv_writer.writerow(row)

    def old_revolve_fitness(self):
        return fitness.online_old_revolve(self)

    def is_evaluated(self):
        """
        Returns true if this robot is at least one full evaluation time old.
        :return:
        """
        return self.age() >= (self.warmup_time + self.conf.evaluation_time)

    def charge(self):
        """
        Returns the remaining battery charge of this robot.
        :return:
        """
        return self.initial_charge - (float(self.age()) * self.size)

    def inverse_charge(self):
        """
        Returns the remaining battery charge of this robot.
        :return:
        """
        return self.initial_charge - (float(self.age()) / self.size)

    def did_mate_with(self, other):
        """
        Called when this robot mated with another robot successfully.
        :param other:
        :type other: RobotManager
        :return:
        """
        self.last_mate = self.last_update

        if other.name in self.mated_with:
            self.mated_with[other.name] += 1
        else:
            self.mated_with[other.name] = 1
