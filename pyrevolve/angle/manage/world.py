from __future__ import absolute_import
from __future__ import print_function

import csv
import os
import pickle
import shutil
import sys
import traceback

from asyncio import Future
from datetime import datetime
from pygazebo.msg import gz_string_pb2

from pyrevolve.sdfbuilder.math import Vector3
from pyrevolve.spec.msgs import BoundingBox
from pyrevolve.spec.msgs import ModelInserted
from pyrevolve.spec.msgs import RobotStates
from .robot import Robot
from ...gazebo import manage
from ...gazebo import RequestHandler
from ...logging import logger
from ...util import multi_future
from ...util import Time


class WorldManager(manage.WorldManager):
    """
    A WorldManager utility class with methods more suited to
    Revolve.Angle, such as inserting whole robot trees etc.
    """

    def __init__(
            self,
            builder,
            generator,
            world_address=None,
            output_directory=None,
            state_update_frequency=None,
            restore=None,
            _private=None
    ):
        """

        :param restore: Restore the world from this directory, if available.
                        Only works if `output_directory` is also specified.
        :param state_update_frequency:
        :param generator:
        :param _private:
        :param world_address:
        :param analyzer_address:
        :param builder:
        :param output_directory:
        :return:
        """
        super(WorldManager, self).__init__(
                _private=_private,
                world_address=world_address,
        )

        self.battery_handler = None

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

        self.state_update_frequency = state_update_frequency
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
                restore = datetime.now()\
                    .strftime(datetime.now().strftime('%Y%m%d%H%M%S'))

            self.output_directory = os.path.join(output_directory, restore)

            if not os.path.exists(self.output_directory):
                os.mkdir(self.output_directory)

            self.snapshot_filename = \
                os.path.join(self.output_directory, 'snapshot.pickle')
            if os.path.exists(self.snapshot_filename):
                # Snapshot exists - restore from it
                with open(self.snapshot_filename, 'rb') as snapshot_file:
                    try:
                        self.do_restore = pickle.load(snapshot_file)
                    except Exception as e:
                        traceback.print_exc()
                        print("Cannot restore snapshot, shutting down. "
                              "Exception: {}.".format(str(e)))
                        sys.exit(23)

            self.world_snapshot_filename = \
                os.path.join(self.output_directory, 'snapshot.world')

            self.robots_filename = \
                os.path.join(self.output_directory, 'robots.csv')
            self.poses_filename = \
                os.path.join(self.output_directory, 'poses.csv')

            if self.do_restore:
                # Copy snapshot files and open created files in append mode
                # TODO: Delete robot sdf / pb files that were created after
                # the snapshot
                shutil.copy(self.poses_filename+'.snapshot', self.poses_filename)
                shutil.copy(self.robots_filename+'.snapshot', self.robots_filename)

                self.robots_file = open(self.robots_filename, 'ab')
                self.poses_file = open(self.poses_filename, 'ab')
                self.write_robots = csv.writer(self.robots_file, delimiter=',')
                self.write_poses = csv.writer(self.poses_file, delimiter=',')
            else:
                # Open poses file, this is written *a lot* so use default OS
                # buffering
                poses_log = os.path.join(self.output_directory, 'poses.csv')
                self.poses_file = open(poses_log, 'wt')

                # Open robots file line buffered so we can see it on the fly,
                # isn't written too often.
                robot_log = os.path.join(self.output_directory, 'robots.csv')
                self.robots_file = open(robot_log, 'wt', buffering=1)
                self.write_robots = csv.writer(self.robots_file, delimiter=',')
                self.write_poses = csv.writer(self.poses_file, delimiter=',')

                self.write_robots.writerow(self.robots_header())
                self.write_poses.writerow(self.poses_header())

    def robots_header(self):
        """
        Returns the header to be written to the robots file
        :return:
        """
        return ['id', 'parent1', 'parent2', 'battery_level']

    def poses_header(self):
        """
        Returns the header to be written to the poses file
        :return:
        """
        return ['id', 'sec', 'nsec', 'x', 'y', 'z', 'battery_level']

    @classmethod
    async def create(
            cls,
            world_address=("127.0.0.1", 11345),
            pose_update_frequency=10
    ):
        """
        Coroutine to instantiate a Revolve.Angle WorldManager
        :param pose_update_frequency:
        :param world_address:
        :param analyzer_address:
        :return:
        """
        self = cls(
                _private=cls._PRIVATE,
                world_address=world_address,
                state_update_frequency=pose_update_frequency
        )
        await (self._init(builder=None, generator=None))
        return (self)

    async def teardown(self):
        """
        Finalizes the world, flushes files, etc.
        :return:
        """
        if self.robots_file:
            self.robots_file.close()
            self.poses_file.close()

    async def _init(self):
        """
        Initializes the world manager
        :return:
        """
        if self.manager is not None:
            return

        await (super(WorldManager, self)._init())

        # Subscribe to pose updates
        self.pose_subscriber = self.manager.subscribe(
            '/gazebo/default/revolve/robot_states',
            'revolve.msgs.RobotStates',
            self._update_states
        )

        await (self.set_state_update_frequency(
                freq=self.state_update_frequency
        ))

        self.battery_handler = await (RequestHandler.create(
                manager=self.manager,
                advertise='/gazebo/default/battery_level/request',
                subscribe='/gazebo/default/battery_level/response',
                # There will not be robots yet, so don't wait for this
                wait_for_publisher=False,
                wait_for_subscriber=False
        ))

        # Wait for connections
        await (self.pose_subscriber.wait_for_connection())

        if self.do_restore:
            await (self.restore_snapshot(self.do_restore))

    async def create_snapshot(self):
        """
        Creates a snapshot of the world in the output directory.
        This pauses the world.
        :return:
        """
        if not self.output_directory:
            logger.warning("No output directory - no snapshot will be created.")
            return False

        # Pause the world
        await (self.pause())

        # Obtain a copy of the current world SDF from Gazebo and write it to
        # file
        response = await (self.request_handler.do_gazebo_request(
                request="world_sdf"
        ))
        if response.response == "error":
            logger.warning("WARNING: requesting world state resulted in "
                           "error. Snapshot failed.")
            return False

        msg = gz_string_pb2.GzString()
        msg.ParseFromString(response.serialized_data)
        with open(self.world_snapshot_filename, 'wb') as f:
            f.write(msg.data)

        # Get the snapshot data and pickle to file
        data = await (self.get_snapshot_data())

        # It seems pickling causes some issues with the default recursion
        # limit, up it
        sys.setrecursionlimit(10000)
        with open(self.snapshot_filename, 'wb') as f:
            pickle.dump(data, f, protocol=-1)

        # Flush statistic files and copy them
        self.poses_file.flush()
        self.robots_file.flush()
        shutil.copy(self.poses_filename, self.poses_filename+'.snapshot')
        shutil.copy(self.robots_filename, self.robots_filename+'.snapshot')
        return True

    async def restore_snapshot(self, data):
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

    async def get_snapshot_data(self):
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

    async def set_state_update_frequency(self, freq):
        """
        Sets the pose update frequency. Defaults to 10 times per second.
        :param freq:
        :type freq: int
        :return:
        """
        future = await (self.request_handler.do_gazebo_request(
                request="set_robot_state_update_frequency",
                data=str(freq)
        ))
        self.state_update_frequency = freq
        return future

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
        return list(self.robots.values())

    def get_robot_by_name(self, name):
        """
        :param name:
        :return:
        :rtype: Robot|None
        """
        return self.robots.get(name, None)

    async def generate_valid_robot(self, max_attempts=100):
        """
        Uses tree generation in conjuction with the analyzer
        to generate a valid new robot.

        :param max_attempts:  Maximum number of tries before giving up.
        :type max_attempts: int
        :return:
        """
        for _ in range(max_attempts):
            tree = self.generator.generate_tree()

            ret = await self.analyze_tree(tree)
            if ret is None:
                # Error already shown
                continue

            coll, bbox, robot = ret
            if not coll:
                return tree, robot, bbox

        logger.error("Failed to produce a valid robot in {} attempts."
                     .format(max_attempts))
        return None

    async def analyze_tree(self, tree):
        """
        Calls the body analyzer on a robot tree.
        :param tree:
        :return:
        """
        robot = tree.to_protobot(self.get_robot_id())

        # TODO: Fix this by sending SDF to Gazebo and returning a bounding box
        bbox = BoundingBox()
        bbox.min.x = -0.045
        bbox.min.y = -0.240100062445
        bbox.min.z = -0.0225
        bbox.max.x = 0.175792043339
        bbox.max.y = 0.120400062445
        bbox.max.z = 0.0225

        # coll, bbox = ret
        coll = 0
        return coll, bbox, robot

    async def insert_robot(
            self,
            py_bot,
            pose,
            name=None,
            initial_battery=0.0,
            parents=None
    ):
        """
        Inserts a robot into the world. This consists of two steps:

        - Sending the insert request message
        - Receiving a ModelInfo response

        This method is a coroutine because of the first step, writing
        the message must be yielded since PyGazebo doesn't appear to
        support writing multiple messages simultaneously. For the response,
        i.e. the message that confirms the robot has been inserted, a
        future is returned.

        :param py_bot:
        :type py_bot: Python tree structure of a robot
        :param pose: Insertion pose of a robot
        :type pose: Pose
        :param name: (Unique) name of a robot
        :type name: str
        :param initial_battery: Initial battery level
        :param parents:
        :return: A future that resolves with the created `Robot` object.
        """
        robot_id = self.get_robot_id()
        robot_name = "gen__"+str(robot_id) \
            if name is None else str(name)

        proto_bot = py_bot.to_protobot(robot_id)
        sdf_bot = self.to_sdfbot(
                robot=proto_bot,
                robot_name=robot_name,
                initial_battery=initial_battery)
        sdf_bot.elements[0].set_pose(pose)

        if self.output_directory:
            robot_file_path = os.path.join(
                    self.output_directory,
                    'robot_{}.sdf'.format(robot_id)
            )
            with open(robot_file_path, 'w') as f:
                f.write(str(sdf_bot))

        future = Future()
        insert_future = await self.insert_model(sdf_bot)
        # TODO: Unhandled error in exception handler. Fix this.
        insert_future.add_done_callback(lambda fut: self._robot_inserted(
                robot_name=robot_name,
                tree=py_bot,
                robot=proto_bot,
                initial_battery=initial_battery,
                parents=parents,
                msg=fut.result(),
                return_future=future
        ))
        return future

    def to_sdfbot(
            self,
            robot,
            robot_name,
            initial_battery=0.0
    ):
        """

        :param initial_battery:
        :param robot:
        :type robot: PbRobot
        :param robot_name:
        :return:
        :rtype: SDF
        """
        raise NotImplementedError(
                "Implement in subclass if you want to use this method.")

    async def delete_robot(self, robot):
        """
        :param robot:
        :type robot: Robot
        :return:
        """
        # Immediately unregister the robot so no it won't be used
        # for anything else while it is being deleted.
        self.unregister_robot(robot)
        future = await (self.delete_model(robot.name, req="delete_robot"))
        return future

    async def delete_all_robots(self):
        """
        Deletes all robots from the world. Returns a future that resolves
        when all responses have been received.
        :return:
        """
        futures = []
        for bot in list(self.robots.values()):
            future = await (self.delete_robot(bot))
            futures.append(future)

        return multi_future(futures)

    def _robot_inserted(
            self,
            robot_name,
            tree,
            robot,
            initial_battery,
            parents,
            msg,
            return_future
    ):
        """
        Registers a newly inserted robot and marks the insertion
        message response as handled.

        :param tree:
        :param robot_name:
        :param tree:
        :param robot:
        :param initial_battery:
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

        robot = self.create_robot_manager(
                robot_name,
                tree,
                robot,
                position,
                time,
                initial_battery,
                parents
        )
        self.register_robot(robot)
        return_future.set_result(robot)

    def create_robot_manager(
            self,
            robot_name,
            tree,
            robot,
            position,
            time,
            battery_level,
            parents
    ):
        """
        :param robot_name:
        :param tree:
        :param robot:
        :param position:
        :param time:
        :param battery_level:
        :param parents:
        :return:
        :rtype: Robot
        """
        return Robot(
                name=robot_name,
                tree=tree,
                robot=robot,
                position=position,
                time=time,
                battery_level=battery_level,
                parents=parents
        )

    def register_robot(self, robot):
        """
        Registers a robot with its Gazebo ID in the local array.
        :param robot:
        :type robot: Robot
        :return:
        """
        logger.debug("Registering robot {}.".format(robot.name))

        if robot.name in self.robots:
            raise ValueError("Duplicate robot: {}".format(robot.name))

        self.robots[robot.name] = robot
        if self.output_directory:
            # Write robot details and CSV row to files
            proto_file = '{}/robot_{}.pb'.format(
                    self.output_directory,
                    robot.robot.id)
            robot.write_robot(
                    details_file=proto_file,
                    csv_writer=self.write_robots)

    def unregister_robot(self, robot):
        """
        Unregisters the robot with the given ID, usually happens when
        it is deleted.
        :param robot:
        :type robot: Robot
        :return:
        """
        logger.debug("Unregistering robot {}.".format(robot.name))
        del self.robots[robot.name]

    async def reset(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        self.start_time = None
        self.last_time = None
        future = await (super(WorldManager, self).reset(**kwargs))
        return future

    async def update_battery_level(self, robot):
        """
        Communicates a single robot's battery level to its
        controller.
        :param robot:
        :return:
        """
        future = await (self.battery_handler.do_gazebo_request(
                request="set_battery_level",
                data=robot.name,
                dbl_data=robot.get_battery_level()
        ))
        return future

    async def update_battery_levels(self):
        """
        Communicates battery levels for all active robots.
        :return:
        """
        futures = []
        for robot in self.robot_list():
            fut = await (self.update_battery_level(robot))
            futures.append(fut)

        if futures:
            return multi_future(futures)

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

    def _update_states(self, msg):
        """
        Handles the pose info message by updating robot positions.
        :param msg:
        :return:
        """
        states = RobotStates()
        states.ParseFromString(msg)

        self.last_time = t = Time(msg=states.time)
        if self.start_time is None or t < self.start_time:
            # A lower start time may indicate a world reset, which
            # we should copy.
            self.start_time = t

        for state in states.robot_state:
            robot = self.robots.get(state.name, None)
            if not robot:
                continue

            robot.update_state(self, t, state, self.write_poses)

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
