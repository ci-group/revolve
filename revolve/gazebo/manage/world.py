# Global / system
import trollius
from trollius import From, Return
import time
from pygazebo.msg import world_control_pb2

# Revolve
from ..connect import connect, RequestHandler
from ..analyze import BodyAnalyzer
from ...logging import logger

# Construct a message base from the time. This should make
# it unique enough for consecutive use when the script
# is restarted.
_a = time.time()
MSG_BASE = int(_a - 14e8 + (_a - int(_a)) * 1e5)


class WorldManager(object):
    """
    Class for basic world management such as inserting / deleting
    models
    """
    # Object used to make constructor private
    _PRIVATE = object()

    def __init__(self, _private=None, world_address=None, analyzer_address=None):
        """

        :param _private:
        :return:
        """
        if _private is not self._PRIVATE:
            raise ValueError("The manager cannot be directly constructed,"
                             "rather the `create` coroutine should be used.")

        self.world_address = world_address
        self.analyzer_address = analyzer_address

        self.manager = None
        self.analyzer = None
        self.world_control = None

    @classmethod
    @trollius.coroutine
    def create(cls, world_address=("127.0.0.1", 11345), analyzer_address=("127.0.0.1", 11346)):
        """

        :param analyzer_address:
        :param world_address:
        :return:
        """
        self = cls(_private=cls._PRIVATE, world_address=world_address, analyzer_address=analyzer_address)
        yield From(self._init())
        raise Return(self)

    def _init(self):
        """
        Initializes connections for the world manager
        :return:
        """
        if self.manager is not None:
            return

        # Initialize the manager / analyzer connections as well as
        # the general request handler
        self.manager = yield From(connect(self.world_address))

        if self.analyzer_address:
            self.analyzer = yield From(BodyAnalyzer.create(self.analyzer_address))

        self.world_control = yield From(self.manager.advertise(
            '/gazebo/default/world_control', 'gazebo.msgs.WorldControl'
        ))

        self.request_handler = yield From(RequestHandler.create(
            self.manager, msg_id_base=MSG_BASE))

        # Wait for connections
        yield From(self.world_control.wait_for_listener())

    @trollius.coroutine
    def pause(self, pause=True):
        """
        Pause / unpause the world
        :param pause:
        :return: Future for the published message
        """
        if pause:
            logger.debug("Pausing the world.")
        else:
            logger.debug("Resuming the world.")

        msg = world_control_pb2.WorldControl()
        msg.pause = pause
        yield From(self.world_control.publish(msg))

    @trollius.coroutine
    def reset(self):
        """
        Reset the world
        :return:
        """
        logger.debug("Resetting the world state.")
        msg = world_control_pb2.WorldControl()
        msg.reset.all = True
        yield From(self.world_control.publish(msg))

    @trollius.coroutine
    def insert_model(self, sdf):
        """
        Insert a model wrapped in an SDF tag into the world. Make
        sure it has a unique name, as it will be literally inserted into the world.

        This coroutine yields until the request has been successfully sent.
        It returns a future that resolves when a response has been received. The
        optional given callback is added to this future.

        :param sdf:
        :type sdf: SDF
        :return:
        """
        future = yield From(self.request_handler.do_gazebo_request("insert_sdf", data=str(sdf)))
        raise Return(future)

    @trollius.coroutine
    def delete_model(self, name, req="entity_delete"):
        """
        Deletes the model with the given name from the world.
        :param name:
        :param req: Type of request to use. If you are going to
        delete a robot, I suggest using `delete_robot` rather than `entity_delete`
        because this attempts to prevent some issues with segmentation faults
        occurring from deleting sensors.
        :return:
        """
        future = yield From(self.request_handler.do_gazebo_request(req, data=name))
        raise Return(future)
