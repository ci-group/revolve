# Global imports
import os
import shutil
import pickle
from datetime import datetime
import csv
import trollius
from trollius import From, Return, Future
from sdfbuilder import SDF
from sdfbuilder.math import Vector3
from pygazebo.msg import poses_stamped_pb2, gz_string_pb2

# Local imports
from ...gazebo import manage
from ...spec import Robot as PbRobot
from .robot import Robot
from ...logging import logger
from ...util import multi_future, Time, wait_for
from revolve.spec.msgs import ModelInserted


class WorldManager(manage.WorldManager):
    """
    A WorldManager utility class with methods more suited to
    Revolve.Angle, such as inserting whole robot trees etc.
    """

    def __init__(self, builder, generator, world_address=None, analyzer_address=None,
                 output_directory=None, pose_update_frequency=None,
                 restore=None, _private=None):
        """

        :param restore: Restore the world from this directory, if available. Only works
                         if `output_directory` is also specified.
        :param pose_update_frequency:
        :param generator:
        :param _private:
        :param world_address:
        :param analyzer_address:
        :param builder:
        :param output_directory:
        :return:
        """
        super(WorldManager, self).__init__(_private=_private, world_address=world_address,
                                           analyzer_address=analyzer_address)

        # Output files for robot CSV data
        self.robots_file = None
        self.poses_file = None
        self.write_robots = None
        self.write_poses = None
        self.output_directory = None
        self.robots_filename = None
        self.poses_filename = None
        self.snapshot_filename = None
        self.world_snapshot_filename = None

        self.pose_update_frequency = pose_update_frequency
        self.builder = builder
        self.generator = generator

        self.robots = {}
        self.robot_id = 0

        self.start_time = None
        self.last_time = None

        # List of functions called when the local state updates
        self.update_triggers = []

        self.do_restore = None

        if output_directory:
            if not restore:
                restore = datetime.now().strftime(datetime.now().strftime('%Y%m%d%H%M%S'))

            self.output_directory = os.path.join(output_directory, restore)

            if not os.path.exists(self.output_directory):
                os.mkdir(self.output_directory)

            self.snapshot_filename = os.path.join(self.output_directory, 'snapshot.pickle')
            if os.path.exists(self.snapshot_filename):
                # Snapshot exists - restore from it
                with open(self.snapshot_filename, 'rb') as snapshot_file:
                    self.do_restore = pickle.load(snapshot_file)

            self.world_snapshot_filename = os.path.join(self.output_directory, 'snapshot.world')

            self.robots_filename = os.path.join(self.output_directory, 'robots.csv')
            self.poses_filename = os.path.join(self.output_directory, 'poses.csv')

            if self.do_restore:
                # Copy snapshot files and open created files in append mode
                # TODO Delete robot sdf / pb files that were created after the snapshot
                shutil.copy(self.poses_filename+'.snapshot', self.poses_filename)
                shutil.copy(self.robots_filename+'.snapshot', self.robots_filename)

                self.robots_file = open(self.robots_filename, 'ab')
                self.poses_file = open(self.poses_filename, 'ab')
                self.write_robots = csv.writer(self.robots_file, delimiter=',')
                self.write_poses = csv.writer(self.poses_file, delimiter=',')
            else:
                # Open poses file, this is written *a lot* so use default OS buffering
                self.poses_file = open(os.path.join(self.output_directory, 'poses.csv'), 'wb')

                # Open robots file line buffered so we can see it on the fly, isn't written
                # too often.
                self.robots_file = open(os.path.join(self.output_directory, 'robots.csv'), 'wb', buffering=1)
                self.write_robots = csv.writer(self.robots_file, delimiter=',')
                self.write_poses = csv.writer(self.poses_file, delimiter=',')

                self.write_robots.writerow(self.robots_header())
                self.write_poses.writerow(self.poses_header())

    def robots_header(self):
        """
        Returns the header to be written to the robots file
        :return:
        """
        return ['id', 'parent1', 'parent2']

    def poses_header(self):
        """
        Returns the header to be written to the poses file
        :return:
        """
        return ['id', 'sec', 'nsec', 'x', 'y', 'z']

    @classmethod
    @trollius.coroutine
    def create(cls, world_address=("127.0.0.1", 11345), analyzer_address=("127.0.0.1", 11346),
               pose_update_frequency=10):
        """
        Coroutine to instantiate a Revolve.Angle WorldManager
        :param pose_update_frequency:
        :param world_address:
        :param analyzer_address:
        :return:
        """
        self = cls(_private=cls._PRIVATE, world_address=world_address, analyzer_address=analyzer_address,
                   pose_update_frequency=pose_update_frequency)
        yield From(self._init())
        raise Return(self)

    @trollius.coroutine
    def teardown(self):
        """
        Finalizes the world, flushes files, etc.
        :return:
        """
        if self.robots_file:
            self.robots_file.close()
            self.poses_file.close()

    @trollius.coroutine
    def _init(self):
        """
        Initializes the world manager
        :return:
        """
        if self.manager is not None:
            return

        yield From(super(WorldManager, self)._init())

        # Subscribe to pose updates
        self.pose_subscriber = self.manager.subscribe(
            '/gazebo/default/revolve/robot_poses',
            'gazebo.msgs.PosesStamped',
            self._update_poses
        )

        fut = yield From(self.set_pose_update_frequency(self.pose_update_frequency))
        yield From(fut)

        # Wait for connections
        yield From(self.pose_subscriber.wait_for_connection())

        if self.do_restore:
            yield From(self.restore_snapshot(self.do_restore))

    @trollius.coroutine
    def create_snapshot(self):
        """
        Creates a snapshot of the world in the output directory. This pauses the world.
        :return:
        """
        if not self.output_directory:
            logger.warning("No output directory - no snapshot will be created.")
            raise Return(False)

        # Pause the world
        yield From(wait_for(self.pause()))

        # Obtain a copy of the current world SDF from Gazebo and write it to file
        response = yield From(wait_for(self.request_handler.do_gazebo_request("world_sdf")))
        if response.response == "error":
            logger.warning("WARNING: requesting world state resulted in error. Snapshot failed.")
            raise Return(False)

        msg = gz_string_pb2.GzString()
        msg.ParseFromString(response.serialized_data)
        with open(self.world_snapshot_filename, 'wb') as f:
            f.write(msg.data)

        # Get the snapshot data and pickle to file
        data = yield From(self.get_snapshot_data())

        with open(self.snapshot_filename, 'wb') as f:
            pickle.dump(data, f)

        # Flush statistic files and copy them
        self.poses_file.flush()
        self.robots_file.flush()
        shutil.copy(self.poses_filename, self.poses_filename+'.snapshot')
        shutil.copy(self.robots_filename, self.robots_filename+'.snapshot')
        raise Return(True)

    @trollius.coroutine
    def restore_snapshot(self, data):
        """
        Called with the data object created and pickled in `get_snapshot_data`,
        should restore the state of the world manager to where
        it can continue the way it left off.
        :param data:
        :return:
        """
        self.robots = data['robots']
        self.robot_id = data['robot_id']
        self.start_time = data['start_time']
        self.last_time = data['last_time']

    @trollius.coroutine
    def get_snapshot_data(self):
        """
        Returns a data object to be pickled into a snapshot file.
        This should contain
        :return:
        """
        return {
            "robots": self.robots,
            "robot_id": self.robot_id,
            "start_time": self.start_time,
            "last_time": self.last_time
        }

    def set_pose_update_frequency(self, freq):
        """
        Sets the pose update frequency. Defaults to 10 times per second.
        :param freq:
        :type freq: int
        :return:
        """
        fut = yield From(self.request_handler.do_gazebo_request("set_robot_pose_update_frequency", str(freq)))
        self.pose_update_frequency = freq
        raise Return(fut)

    def get_robot_id(self):
        """
        Robot ID sequencer
        :return:
        """
        self.robot_id += 1
        return self.robot_id

    def robot_list(self):
        """
        Returns the list of registered robots
        :return:
        :rtype: list[Robot]
        """
        return self.robots.values()

    def get_robot_by_name(self, name):
        """
        :param name:
        :return:
        :rtype: Robot|None
        """
        return self.robots.get(name, None)

    @trollius.coroutine
    def generate_valid_robot(self, max_attempts=100):
        """
        Uses tree generation in conjuction with the analyzer
        to generate a valid new robot.

        :param max_attempts:  Maximum number of tries before giving up.
        :type max_attempts: int
        :return:
        """
        for i in xrange(max_attempts):
            tree = self.generator.generate_tree()

            ret = yield From(self.analyze_tree(tree))
            if ret is None:
                # Error already shown
                continue

            coll, bbox, robot = ret
            if not coll:
                raise Return(tree, robot, bbox)

        logger.error("Failed to produce a valid robot in %d attempts." % max_attempts)
        raise Return(None)

    @trollius.coroutine
    def analyze_tree(self, tree):
        """
        Calls the body analyzer on a robot tree.
        :param tree:
        :return:
        """
        if not self.analyzer:
            raise RuntimeError("World.analyze_tree(): No analyzer configured.")

        robot = tree.to_robot(self.get_robot_id())
        ret = yield From(self.analyzer.analyze_robot(robot, builder=self.builder))
        if ret is None:
            logger.error("Error in robot analysis, skipping.")
            raise Return(None)

        coll, bbox = ret
        raise Return(coll, bbox, robot)

    @trollius.coroutine
    def insert_robot(self, tree, pose, parents=None):
        """
        Inserts a robot into the world. This consists of two steps:

        - Sending the insert request message
        - Receiving a ModelInfo response

        This method is a coroutine because of the first step, writing
        the message must be yielded since PyGazebo doesn't appear to
        support writing multiple messages simultaneously. For the response,
        i.e. the message that confirms the robot has been inserted, a
        future is returned.

        :param parents:
        :param tree:
        :type tree: Tree
        :param pose:
        :type pose: Pose
        :return: A future that resolves with the created `Robot` object.
        """
        robot_id = self.get_robot_id()
        robot_name = "gen__"+str(robot_id)

        robot = tree.to_robot(robot_id)
        sdf = self.get_simulation_sdf(robot, robot_name)
        sdf.elements[0].set_pose(pose)

        if self.output_directory:
            with open(os.path.join(self.output_directory, 'robot_%d.sdf' % robot_id), 'w') as f:
                f.write(str(sdf))

        return_future = Future()
        insert_future = yield From(self.insert_model(sdf))
        insert_future.add_done_callback(lambda fut: self._robot_inserted(
            robot_name, tree, robot, parents, fut.result(), return_future
        ))
        raise Return(return_future)

    def get_simulation_sdf(self, robot, robot_name):
        """

        :param robot:
        :type robot: PbRobot
        :param robot_name:
        :return:
        :rtype: SDF
        """
        raise NotImplementedError("Implement in subclass if you want to use this method.")

    @trollius.coroutine
    def delete_robot(self, robot):
        """
        :param robot:
        :type robot: Robot
        :return:
        """
        # Immediately unregister the robot so no it won't be used
        # for anything else while it is being deleted.
        self.unregister_robot(robot)
        future = yield From(self.delete_model(robot.name, req="delete_robot"))
        raise Return(future)

    @trollius.coroutine
    def delete_all_robots(self):
        """
        Deletes all robots from the world. Returns a future that resolves
        when all responses have been received.
        :return:
        """
        futures = []
        for bot in self.robots.values():
            future = yield From(self.delete_robot(bot))
            futures.append(future)

        raise Return(multi_future(futures))

    def _robot_inserted(self, robot_name, tree, robot, parents, msg, return_future):
        """
        Registers a newly inserted robot and marks the insertion
        message response as handled.

        :param tree:
        :param robot_name:
        :param tree:
        :param robot:
        :param parents:
        :param msg:
        :type msg: pygazebo.msgs.response_pb2.Response
        :param return_future: Future to resolve with the created robot object.
        :type return_future: Future
        :return:
        """
        inserted = ModelInserted()
        inserted.ParseFromString(msg.serialized_data)
        model = inserted.model
        time = Time(msg=inserted.time)
        p = model.pose.position
        position = Vector3(p.x, p.y, p.z)

        robot = self.create_robot_manager(robot_name, tree, robot, position, time, parents)
        self.register_robot(robot)
        return_future.set_result(robot)

    def create_robot_manager(self, robot_name, tree, robot, position, time, parents):
        """
        :param robot_name:
        :param tree:
        :param robot:
        :param position:
        :param time:
        :param parents:
        :return:
        :rtype: Robot
        """
        return Robot(robot_name, tree, robot, position, time, parents=parents)

    def register_robot(self, robot):
        """
        Registers a robot with its Gazebo ID in the local array.
        :param robot:
        :type robot: Robot
        :return:
        """
        logger.debug("Registering robot %s." % robot.name)

        if robot.name in self.robots:
            raise ValueError("Duplicate robot: %s" % robot.name)

        self.robots[robot.name] = robot
        if self.output_directory:
            # Write robot details and CSV row to files
            robot.write_robot(self, '%s/robot_%d.pb' % (self.output_directory, robot.robot.id),
                              self.write_robots)

    def unregister_robot(self, robot):
        """
        Unregisters the robot with the given ID, usually happens when
        it is deleted.
        :param robot:
        :type robot: Robot
        :return:
        """
        logger.debug("Unregistering robot %s." % robot.name)
        del self.robots[robot.name]

    @trollius.coroutine
    def reset(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        self.start_time = None
        fut = yield From(super(WorldManager, self).reset(**kwargs))
        raise Return(fut)

    def age(self):
        """
        Returns the age of the world, i.e. the difference between the
        first and last registered update times.
        :return:
        :rtype: Time
        """
        if self.start_time is None:
            return Time()
        else:
            return self.last_time - self.start_time

    def _update_poses(self, msg):
        """
        Handles the pose info message by updating robot positions.
        :param msg:
        :return:
        """
        poses = poses_stamped_pb2.PosesStamped()
        poses.ParseFromString(msg)

        self.last_time = t = Time(msg=poses.time)
        if self.start_time is None:
            self.start_time = t

        for pose in poses.pose:
            robot = self.robots.get(pose.name, None)
            if not robot:
                continue

            position = Vector3(pose.position.x, pose.position.y, pose.position.z)
            robot.update_position(t, position, self.write_poses)

        self.call_update_triggers()

    def add_update_trigger(self, callback):
        """
        Adds an update trigger, a function called every time the local
        state is updated.
        :param callback:
        :type callback: callable
        :return:
        """
        self.update_triggers.append(callback)

    def remove_update_trigger(self, callback):
        """
        Removes a previously installed update trigger.
        :param callback:
        :type callback: callable
        :return:
        """
        self.update_triggers.remove(callback)

    def call_update_triggers(self):
        """
        Calls all update triggers.
        :return:
        """
        for callback in self.update_triggers:
            callback(self)
