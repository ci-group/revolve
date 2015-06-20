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
from .connect import connect

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
    running doing other things, look at `analysis_coroutine()`
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
    msg_id = _msg_id()
    response_obj = [None]

    @trollius.coroutine
    def internal_analyze():
        manager = yield From(connect(address))
        response_obj[0] = yield From(analysis_coroutine(sdf, msg_id, manager))

    loop = trollius.get_event_loop()
    loop.run_until_complete(internal_analyze())
    return response_obj[0]


@trollius.coroutine
def attach_analyzer(manager):
    """
    Attaches the body analyzer to the given manager.
    :param manager:
    :type manager: Manager
    :return:
    """
    analyzer = getattr(manager, 'rvgz_analyzer', None)

    if analyzer:
        # _Analyzer already attached
        raise Return(analyzer)

    analyzer = _Analyzer(manager)
    setattr(manager, 'rvgz_analyzer', analyzer)
    yield From(analyzer.initialize())
    raise Return(analyzer)

@trollius.coroutine
def message_coroutine(sdf, manager):
    """
    Coroutine that connects to Gazebo, performs analysis, and
    returns the result of the analysis message.
    :param sdf:
    :param manager:
    :type manager: Manager
    :return:
    """
    # Attach the analyzer if not already attached
    analyzer = yield From(attach_analyzer(manager))
    publisher = analyzer.publisher

    msg_id = _msg_id()
    message = AnalyzeRequest()
    message.id = msg_id
    message.request = "analyze_body"
    message.data = str(sdf)

    # Make sure someone is listening
    yield From(publisher.publish(message))

    response = analyzer.get_response(msg_id)
    while not response:
        yield From(trollius.sleep(0.05))
        response = analyzer.get_response(msg_id)

    # Remove from message history
    analyzer.handled(msg_id)
    raise Return(response)


@trollius.coroutine
def analysis_coroutine(sdf, manager, max_attempts=5):
    """
    Coroutine that returns with a (collisions, bounding box) tuple,
    assuming analysis succeeds.
    :param sdf:
    :param manager: A pygazebo manager connected to a body analyzer
    :type manager: Manager
    :param max_attempts: Maximum number of analysis attempts
    :return:
    """
    msg = None
    for _ in range(max_attempts):
        msg = yield From(message_coroutine(sdf, manager))

        if msg and msg.success:
            break

    if not msg:
        # Error return
        raise Return(None)

    if msg.HasField("boundingBox"):
        b = msg.boundingBox
        bbox = (b.x, b.y, b.z)
    else:
        bbox = None

    internal_collisions = len(msg.contact)
    raise Return(internal_collisions, bbox)

class _Analyzer(object):
    """
    Analyzer class attached to the manager for internal callbacks.
    Internal use only.
    """

    def __init__(self, manager):
        """
        :param manager:
        :type manager: Manager
        :return:
        """
        self.analyzed = {}
        self.publisher = None
        self.manager = manager

        # Subscribe to the analyzer message
        self.subscriber = manager.subscribe(
            '/gazebo/default/analyze_body/response',
            'revolve.msgs.BodyAnalysisResponse',
            self._callback
        )

    def _callback(self, data):
        """
        Subscriber callback
        """
        response = BodyAnalysisResponse()
        response.ParseFromString(data)
        self.analyzed[response.id] = response

    def handled(self, msg_id):
        """
        Declares the given message ID handled
        :param msg_id:
        """
        if msg_id in self.analyzed:
            del self.analyzed[msg_id]

    def get_response(self, msg_id):
        """
        Returns the analyzer response for the given message ID if
        available, None otherwise.
        """
        return self.analyzed.get(msg_id, None)

    @trollius.coroutine
    def initialize(self):
        self.publisher = yield From(
            self.manager.advertise('/gazebo/default/analyze_body/request',
                                   'gazebo.msgs.request')
        )

        # Make sure someone is listening
        yield From(self.publisher.wait_for_listener())
        yield From(self.subscriber.wait_for_connection())