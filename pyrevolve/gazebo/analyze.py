from pyrevolve.util.logger import logger
from pyrevolve.SDF.math import Vector3
from pyrevolve.spec import BodyAnalysisResponse
from .connect import connect, RequestHandler

# Message ID sequencer, start at some high value to prevent ID clashes
# (don't know if this would ever be a problem though).
_counter = 1234321000


def _msg_id():
    global _counter
    r = _counter
    _counter += 1
    return r


class BodyAnalyzer(object):
    """
    Class used to make body analysis requests.
    """
    _PRIVATE = object()

    def __init__(self, _private, address, port):
        """
        Private constructor - use the `create` coroutine instead.

        :param address:
        :type address: tuple
        :return:
        """
        if _private is not self._PRIVATE:
            raise ValueError("`BodyAnalyzer` must be initialized through "
                             "the `create` coroutine.")

        self.address = address
        self.port = port
        self.manager = None
        self.request_handler = None

    @classmethod
    async def create(cls, address, port):
        """
        Instantiates a new body analyzer at the given address.

        :param address: hostname.
        :param port: host port.
        :return:
        """
        self = cls(cls._PRIVATE, address, port)
        await self._init()
        return self

    async def _init(self):
        """
        BodyAnalyzer initialization coroutine
        :return:
        """
        self.manager = await connect(self.address, self.port)
        self.request_handler = await (
            RequestHandler.create(self.manager, msg_id_base=_msg_id()))

    async def disconnect(self):
        await self.manager.stop()
        await self.request_handler.stop()

    async def analyze_robot(self, robot, max_attempts=5):
        """
        Performs body analysis of a given Robot object.
        :param robot:
        :type robot: Robot
        :param max_attempts:
        :return:
        """
        sdf = robot.to_sdf(pose=Vector3(0, 0, 0))
        ret = await self.analyze_sdf(sdf, max_attempts=max_attempts)
        return ret

    async def analyze_sdf(self, sdf, max_attempts=5):
        """
        Coroutine that returns with a (collisions, bounding box) tuple,
        assuming analysis succeeds.

        :param max_attempts:
        :param sdf:
        :type sdf: SDF
        :return:
        """
        msg = None
        rh = self.request_handler
        for _ in range(max_attempts):
            response = await rh.do_gazebo_request("analyze_body", str(sdf))
            if response.response == "success":
                msg = BodyAnalysisResponse()
                msg.ParseFromString(response.serialized_data)
                break

        if not msg:
            logger.error("analyze_sdf returned not valid message")
            return None

        if msg.HasField("boundingBox"):
            bbox = msg.boundingBox
        else:
            bbox = None

        internal_collisions = len(msg.contact)
        return internal_collisions, bbox
