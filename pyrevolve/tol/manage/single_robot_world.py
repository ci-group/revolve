import numbers
import os

import time

from SDF.math import Vector3
from pyrevolve.gazebo.manage import WorldManager
from .learningrobotmanager import LearningRobotManager
from pyrevolve.spec.msgs import LearningRobotStates
from pyrevolve.spec.msgs import ModelInserted
from pyrevolve.util import Time
from pyrevolve.custom_logging.logger import logger

# Construct a message base from the time. This should make it unique enough
# for consecutive use when the script is restarted.
_a = time.time()
MSG_BASE = int(_a - 14e8 + (_a - int(_a)) * 1e5)


class SingleRobotWorld(WorldManager):
    """
    A class that is used to manage the world, meaning it provides methods to
    insert / remove robots and request information about where they are.

    The world class contains a number of coroutines, usually from a
    request/response perspective. These methods thus work with two futures -
    one for the request to complete, one for the response to arrive. The
    convention for these methods is to always yield the first future, because it
    has proven problematic to send multiple messages over the same channel,
    so a request is always sent until completion. The methods then return the
    future that resolves when the response is delivered.
    """

    def __init__(self, program_arguments, _private, world_address):
        """
        :param program_arguments:
        """
        world_address = ("127.0.0.1", 11345) if world_address is None else world_address

        super().__init__(
            _private=_private,
            world_address=world_address,
        )

        self.robot_managers = {}
        self.program_arguments = program_arguments

    @classmethod
    async def create(cls, program_arguments, world_address=None):
        """
        Coroutine to instantiate a Revolve.Angle WorldManager
        :param program_arguments:
        :param world_address:
        :return:
        """
        self = cls(_private=cls._PRIVATE, program_arguments=program_arguments, world_address=world_address)
        await self._init()
        return self

    async def _init(self):
        if self.manager is not None:
            return

        await (super()._init())

        # Subscribe to learning states update
        self.learning_states_subscriber = await self.manager.subscribe(
            '/gazebo/default/revolve/robot_reports',
            'revolve.msgs.LearningRobotStates',
            self._process_learning_state
        )

        # There will be no connection until the first learner starts, so waiting here will result in a deadlock
        # await self.learning_states_subscriber.wait_for_connection()

    async def insert_robot(
            self,
            revolve_bot,
            pose=None,
            life_timeout=None,
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

        :param revolve_bot:
        :type revolve_bot: RevolveBot
        :param pose: Insertion pose of a robot
        :type pose: Pose|Vector3
        :param life_timeout: Life span of the robot
        :type life_timeout: float|None
        :return: A future that resolves with the created `Robot` object.
        """
        if pose is None:
            pose = Vector3(0, 0, self.program_arguments.z_start)
        elif isinstance(pose, numbers.Number):
            pose = Vector3(0, 0, pose)
        elif isinstance(pose, Vector3):
            pass
        elif hasattr(pose, '__iter__'):
            pose = Vector3(pose)
        else:
            raise RuntimeError(f"pose can only be Vector3 or number, instead {type(pose)} was found")

        # if the ID is digit, when removing the robot, the simulation will try to remove random stuff from the
        # environment and give weird crash errors
        assert(not str(revolve_bot.id).isdigit())

        sdf_bot = revolve_bot.to_sdf(pose)

        # To debug and save all SDF files, you can uncomment the following code
        # self.output_directory = '/tmp'
        # if self.output_directory:
        #     robot_file_path = os.path.join(
        #         self.output_directory,
        #         'robot_{}.sdf'.format(revolve_bot.id)
        #     )
        #     with open(robot_file_path, 'w') as f:
        #         f.write(sdf_bot)

        response = await self.insert_model(sdf_bot, life_timeout)
        robot_manager = self._robot_inserted(
            robot=revolve_bot,
            msg=response
        )
        return robot_manager

    def _robot_inserted(
            self,
            robot,
            msg
    ):
        """
        Registers a newly inserted robot and marks the insertion
        message response as handled.

        :param robot: RevolveBot
        :param msg:
        :type msg: pygazebo.msgs.response_pb2.Response
        :return:
        """
        inserted = ModelInserted()
        inserted.ParseFromString(msg.serialized_data)
        model = inserted.model
        inserted_time = Time(msg=inserted.time)
        p = model.pose.position
        position = Vector3(p.x, p.y, p.z)

        robot_manager = self.create_robot_manager(
            robot,
            position,
            inserted_time
        )
        self.register_robot(robot_manager)
        return robot_manager

    def register_robot(self, robot_manager):
        """
        Registers a robot with its Gazebo ID in the local array.
        :param robot_manager:
        :type robot_manager: RobotManager
        """
        logger.info("Registering robot {}.".format(robot_manager.name))

        if robot_manager.name in self.robot_managers:
            raise ValueError("Duplicate robot: {}".format(robot_manager.name))

        self.robot_managers[robot_manager.name] = robot_manager

    def _process_learning_state(self, msg):
        """
        Handles the pose info message by updating robot positions.
        :param msg:
        :return:
        """
        report = LearningRobotStates()
        report.ParseFromString(msg)

        robot_name = report.id
        robot_manager = self.robot_managers[robot_name]
        robot_manager.learning_step_done(report)

    def create_robot_manager(
            self,
            robot,
            start_position,
            inserted_time,
    ):
        """
        Overriding with robot manager with more capabilities.
        :param robot:
        :param inserted_time:
        :return:
        """
        return LearningRobotManager(
            program_arguments=self.program_arguments,
            robot=robot,
            start_position=start_position,
            inserted_time=inserted_time,
        )
