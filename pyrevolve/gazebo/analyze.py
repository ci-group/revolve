from __future__ import absolute_import
from __future__ import print_function

import asyncio
import logging
import sys

from pyrevolve.sdfbuilder import SDF
from pyrevolve.sdfbuilder.sensor import Sensor

from ..spec import BodyAnalysisResponse
from .connect import connect, RequestHandler

# Message ID sequencer, start at some high value to prevent ID clashes
# (don't know if this would ever be a problem though).
_counter = 1234321000


def _msg_id():
    global _counter
    r = _counter
    _counter += 1
    return r


# Prevent the trollius logging warning
kl = logging.getLogger("trollius")
kl.addHandler(logging.StreamHandler(sys.stdout))


def get_analysis_robot(robot, builder):
    """
    Creates an SDF model suitable for analysis from a robot object
    and a builder.
    :param robot:
    :type robot: Robot
    :param builder:
    :type builder: BodyBuilder
    :return:
    """
    model = builder.sdf_robot(
            robot=robot,
            controller_plugin=None,
            name="analyze_bot",
            analyzer_mode=True)
    model.remove_elements_of_type(Sensor, recursive=True)
    sdf = SDF()
    sdf.add_element(model)
    return sdf


def analyze_body(sdf, address=("127.0.0.1", 11346)):
    """
    Single body analyzer. Opens a new connection, analyzes the
    body, and returns the result. If you already have a manager
    running doing other things, create an instance of `BodyAnalyzer`
    instead.

    :param sdf: SDF object consisting of BodyPart
                instances.
    :type sdf: SDF
    :param address: Tuple of the hostname and port where the analyzer
                    resides. Note that the default is one up from the default
                    Gazebo port, since it is meant to be used with the
                    `run-analyzer.sh` tool.
    :type address: (str, int)
    :return:
    :rtype: (bool, (float, float, float))
    """
    response_obj = [None]

    async def internal_analyze():
        analyzer = await (BodyAnalyzer.create(address))
        response_obj[0] = await (analyzer.analyze_sdf(sdf))

    loop = asyncio.get_event_loop()
    loop.run_until_complete(internal_analyze())
    return response_obj[0]


class BodyAnalyzer(object):
    """
    Class used to make body analysis requests.
    """
    _PRIVATE = object()

    def __init__(self, _private, address):
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
        self.manager = None
        self.request_handler = None

    @classmethod
    async def create(cls, address=("127.0.0.1", 11346)):
        """
        Instantiates a new body analyzer at the given address.

        :param address: host, port tuple.
        :type address: (str, int)
        :return:
        """
        self = cls(cls._PRIVATE, address)
        await (self._init())
        return self

    async def _init(self):
        """
        BodyAnalyzer initialization coroutine
        :return:
        """
        self.manager = await (connect(self.address))
        self.request_handler = await (
            RequestHandler.create(self.manager, msg_id_base=_msg_id()))

    async def analyze_robot(self, robot, builder, max_attempts=5):
        """
        Performs body analysis of a given Robot object.
        :param robot:
        :type robot: Robot
        :param builder:
        :type builder: Builder
        :param max_attempts:
        :return:
        """
        sdf = get_analysis_robot(robot, builder)
        ret = await (self.analyze_sdf(sdf, max_attempts=max_attempts))
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
            future = await (rh.do_gazebo_request("analyze_body", str(sdf)))
            await future

            response = future.result()
            if response.response == "success":
                msg = BodyAnalysisResponse()
                msg.ParseFromString(response.serialized_data)
                break

        if not msg:
            # Error return
            return None

        if msg.HasField("boundingBox"):
            bbox = msg.boundingBox
        else:
            bbox = None

        internal_collisions = len(msg.contact)
        return internal_collisions, bbox
