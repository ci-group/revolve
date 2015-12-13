from __future__ import print_function
import sys
from pygazebo import Manager
from pygazebo.msg.request_pb2 import Request as AnalyzeRequest
from ..spec import BodyAnalysisResponse
from ..build.sdf import BodyPart
from sdfbuilder import SDF, Link, Model
from sdfbuilder.sensor import Sensor
import trollius
from trollius import From, Return
import logging
from .connect import connect, RequestHandler

# Message ID sequencer, start at some high value to
# prevent ID clashes (don't know if this would ever be
# a problem though).
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
    model = builder.get_sdf_model(robot, analyzer_mode=True, controller_plugin=None, name="analyze_bot")
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
    :param address: Tuple of the hostname and port where the analyzer resides. Note
                    that the default is one up from the default Gazebo port,
                    since it is meant to be used with the `run-analyzer.sh` tool.
    :type address: (str, int)
    :return:
    :rtype: (bool, (float, float, float))
    """
    response_obj = [None]

    @trollius.coroutine
    def internal_analyze():
        analyzer = yield From(BodyAnalyzer.create(address))
        response_obj[0] = yield From(analyzer.analyze_sdf(sdf))

    loop = trollius.get_event_loop()
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
            raise ValueError("`BodyAnalyzer` must be initialized through the `create` coroutine.")

        self.address = address
        self.manager = None
        self.request_handler = None

    @classmethod
    @trollius.coroutine
    def create(cls, address=("127.0.0.1", 11346)):
        """
        Instantiates a new body analyzer at the given address.

        :param address: host, port tuple.
        :type address: (str, int)
        :return:
        """
        self = cls(cls._PRIVATE, address)
        yield From(self._init())
        raise Return(self)

    @trollius.coroutine
    def _init(self):
        """
        BodyAnalyzer initialization coroutine
        :return:
        """
        self.manager = yield From(connect(self.address))
        self.request_handler = yield From(
            RequestHandler.create(self.manager, msg_id_base=_msg_id()))

    @trollius.coroutine
    def analyze_robot(self, robot, builder, max_attempts=5):
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
        ret = yield From(self.analyze_sdf(sdf, max_attempts=max_attempts))
        raise Return(ret)

    @trollius.coroutine
    def analyze_sdf(self, sdf, max_attempts=5):
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
            future = yield From(rh.do_gazebo_request("analyze_body", str(sdf)))
            yield From(future)

            response = future.result()
            if response.response == "success":
                msg = BodyAnalysisResponse()
                msg.ParseFromString(response.serialized_data)
                break

        if not msg:
            # Error return
            raise Return(None)

        if msg.HasField("boundingBox"):
            bbox = msg.boundingBox
        else:
            bbox = None

        internal_collisions = len(msg.contact)
        raise Return(internal_collisions, bbox)
