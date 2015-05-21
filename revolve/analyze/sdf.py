from __future__ import print_function
import sys
from revolve.build.sdf import BodyPart
from revolve.spec import SdfBodyAnalyzeRequest, SdfBodyAnalyzeResponse
from sdfbuilder import SDF, Link
import trollius
from trollius import From
import logging

import pygazebo

# Message ID counter
_counter = 0

# Prevent the trollius logging warning
kl = logging.getLogger("trollius")
kl.addHandler(logging.NullHandler())

def analyze_body(sdf, address=("127.0.0.1", 11346)):
    """
    Single body analyzer. Opens a new connection, analyzes the
    body, and returns the result.

    :param sdf: SDF object consisting of BodyPart
                instances.
    :type sdf: SDF
    :param address: Tuple of the hostname and port where the analyzer resides. Note
                    that the default is one up from the default Gazebo port,
                    since it is meant to be used with the `run-analyzer.sh` tool.
    :type address: tuple(str,int)
    :return:
    """
    global _counter
    msg_id = "analyze_body_%d" % _counter
    _counter += 1

    response_obj = {
        "analyzed": False,
        "message": None
    }
    loop = trollius.get_event_loop()
    loop.run_until_complete(_connector(sdf, msg_id, response_obj, address=address))

    msg = response_obj["message"]
    if not msg.success:
        # Try again
        return analyze_body(sdf)

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

    return internal_collisions, bbox


@trollius.coroutine
def _connector(sdf, msg_id, response_obj, address):
    """
    Internal publish loop function.
    :param sdf:
    :param msg_id:
    :param response_obj:
    :param address:
    :return:
    """
    message = SdfBodyAnalyzeRequest()
    message.id = msg_id
    message.sdf = str(sdf)

    manager = yield From(pygazebo.connect(address=address))

    def callback(data):
        response = SdfBodyAnalyzeResponse()
        response.ParseFromString(data)
        if response.id == msg_id:
            response_obj['analyzed'] = True
            response_obj['message'] = response

    manager.subscribe('/gazebo/default/analyze_body/result',
                      'revolve.msgs.SdfBodyAnalyzeResponse',
                      callback)

    publisher = yield From(
        manager.advertise('/gazebo/default/analyze_body/request',
                          'revolve.msgs.SdfBodyAnalyzeRequest'))

    # Make sure someone is listening
    yield From(publisher.wait_for_listener())

    print("Publishing %s" % msg_id)
    yield From(publisher.publish(message))

    while not response_obj['analyzed']:
        yield From(trollius.sleep(0.05))
