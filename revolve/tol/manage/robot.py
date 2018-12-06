from __future__ import absolute_import
from __future__ import division

from sdfbuilder.math import Vector3

from revolve.angle import Robot as RvRobot
from revolve.util import Time

from ..util.analyze import count_connections, count_extremities, count_joints, \
    count_motors


class Robot(RvRobot):
    """
    Class to manage a single robot
    """

    def __init__(
            self,
            conf,
            name,
            tree,
            robot,
            position,
            time,
            battery_level=0.0,
            parents=None
    ):
        """
        :param conf:
        :param name:
        :param tree:
        :param robot: Protobuf robot
        :param position:
        :type position: Vector3
        :param time:
        :type time: Time
        :param parents:
        :type parents: tuple(Robot, Robot)
        :param battery_level: Battery charge for this robot
        :type battery_level: float
        :return:
        """
        speed_window = int(conf.evaluation_time * conf.pose_update_frequency)
        super(Robot, self).__init__(
                name=name,
                tree=tree,
                robot=robot,
                position=position,
                time=time,
                battery_level=battery_level,
                speed_window=speed_window,
                warmup_time=conf.warmup_time,
                parents=parents
        )

        # Set of robots this bot has mated with
        self.mated_with = {}
        self.last_mate = None
        self.conf = conf
        self.size = len(tree)
        self.battery_level = battery_level
        self.initial_charge = battery_level

    def will_mate_with(self, other):
        """
        Decides whether or not to mate with the other given robot based on
        its position and speed.
        :param other:
        :type other: Robot
        :return:
        """
        if self.age() < self.conf.warmup_time:
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

        my_fitness = self.fitness()
        other_fitness = other.fitness()

        # Only mate with robots with nonzero fitness, check for self
        # zero-fitness to prevent division by zero.
        return other_fitness > 0 and (
            my_fitness == 0 or
            (other_fitness / my_fitness) >= self.conf.mating_fitness_threshold
        )

    def distance_to(self, vec, planar=True):
        """
        Calculates the Euclidean distance from this robot to
        the given vector position.
        :param vec:
        :type vec: Vector3
        :param planar: If true, only x/y coordinates are considered.
        :return:
        """
        diff = self.last_position - vec
        if planar:
            diff.z = 0

        return diff.norm()

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

    def write_robot(self, world, details_file, csv_writer):
        """
        :param world:
        :param details_file:
        :param csv_writer:
        :return:
        """
        with open(details_file, 'w') as f:
            f.write(self.robot.SerializeToString())

        row = [getattr(world, 'current_run', 0), self.robot.id,
               world.age()]
        row += list(self.parent_ids) if self.parent_ids else ['', '']
        row += [self.size, self.last_position.x,
                self.last_position.y, self.last_position.z]

        root = self.tree.root
        inputs, outputs, hidden = root.io_count(recursive=True)
        row += [
            count_extremities(root),
            count_joints(root),
            count_motors(root),
            inputs,
            outputs,
            hidden,
            count_connections(root)
        ]

        csv_writer.writerow(row)

    def fitness(self):
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
        :return:
        """
        age = self.age()
        if age < (0.25 * self.conf.evaluation_time) \
           or age < self.conf.warmup_time:
            # We want at least some data
            return 0.0

        v_fac = self.conf.fitness_velocity_factor
        d_fac = self.conf.fitness_displacement_factor
        s_fac = self.conf.fitness_size_factor
        d = 1.0 - (self.conf.fitness_size_discount * self.size)
        v = d * (d_fac * self.displacement_velocity()
                 + v_fac * self.velocity()
                 + s_fac * self.size)
        return v if v <= self.conf.fitness_limit else 0.0

    def is_evaluated(self):
        """
        Returns true if this robot is at least one full evaluation time old.
        :return:
        """
        return self.age() >= (self.conf.warmup_time + self.conf.evaluation_time)

    def charge(self):
        """
        Returns the remaining battery charge of this robot.
        :return:
        """
        return self.initial_charge - (float(self.age()) * self.size)

    def did_mate_with(self, other):
        """
        Called when this robot mated with another robot successfully.
        :param other:
        :type other: Robot
        :return:
        """
        self.last_mate = self.last_update

        if other.name in self.mated_with:
            self.mated_with[other.name] += 1
        else:
            self.mated_with[other.name] = 1
