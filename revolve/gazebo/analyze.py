from __future__ import print_function
import sys
from pygazebo import Manager
from ..spec import SdfBodyAnalyzeResponse, SdfBodyAnalyzeRequest
from ..build.sdf import BodyPart
from sdfbuilder import SDF, Link
import trollius
from trollius import From, Return
import logging
from .connect import connect

# Message ID counter
_counter = 0

# Prevent the trollius logging warning
kl = logging.getLogger("trollius")
kl.addHandler(logging.NullHandler())

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
    global _counter
    msg_id = "analyze_body_%d" % _counter
    _counter += 1

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
        # Analyzer already attached
        raise Return(analyzer)

    analyzer = Analyzer(manager)
    setattr(manager, 'rvgz_analyzer', analyzer)
    yield From(analyzer.make_publisher())
    raise Return(analyzer)

@trollius.coroutine
def message_coroutine(sdf, msg_id, manager):
    """
    Coroutine that connects to Gazebo, performs analysis, and
    returns the result of the analysis message.
    :param sdf:
    :param msg_id:
    :param manager:
    :type manager: Manager
    :return:
    """
    message = SdfBodyAnalyzeRequest()
    message.id = msg_id
    message.sdf = str(sdf)

    # Attach the analyzer if not already attached
    analyzer = yield From(attach_analyzer(manager))
    publisher = analyzer.publisher

    # Make sure someone is listening
    yield From(publisher.wait_for_listener())
    yield From(publisher.publish(message))

    response = analyzer.get_response(msg_id)
    while not response:
        yield From(trollius.sleep(0.05))
        response = analyzer.get_response(msg_id)

    # Remove from message history
    analyzer.handled(msg_id)
    raise Return(response)


@trollius.coroutine
def analysis_coroutine(sdf, msg_id, manager, max_attempts=5):
    """
    Coroutine that returns with a (collisions, bounding box) tuple,
    assuming analysis succeeds.
    :param sdf:
    :param msg_id:
    :param manager:
    :type manager: Manager
    :param max_attempts: Maximum number of analysis attempts
    :return:
    """
    msg = None
    for _ in range(max_attempts):
        msg = yield From(message_coroutine(sdf, msg_id, manager))

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

    body_parts = sdf.get_elements_of_type(BodyPart, recursive=True)
    link_map = {link.name: body_part
                for body_part in body_parts
                for link in body_part.get_elements_of_type(Link)}

    internal_collisions = False
    for contact in msg.contact:
        # Contacts are of form model_name::link_name::collision_name.
        # We are only interested in link contacts.
        link1 = contact.collision1.split("::")[1]
        link2 = contact.collision2.split("::")[1]

        if link1 not in link_map:
            print("Unknown contact link: '%s'" % link1, file=sys.stderr)
            continue

        if link2 not in link_map:
            print("Unknown contact link: '%s'" % link2, file=sys.stderr)
            continue

        if link_map[link1] is not link_map[link2]:
            internal_collisions = True
            break

    raise Return(internal_collisions, bbox)

class Analyzer(object):
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
        manager.subscribe('/gazebo/default/analyze_body/result',
                          'revolve.msgs.SdfBodyAnalyzeResponse',
                          self._callback)

    def _callback(self, data):
        """
        Subscriber callback
        """
        response = SdfBodyAnalyzeResponse()
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
    def make_publisher(self):
        self.publisher = yield From(
            self.manager.advertise('/gazebo/default/analyze_body/request',
                                   'revolve.msgs.SdfBodyAnalyzeRequest')
        )
