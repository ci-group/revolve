from sdfbuilder import SDF
from ..spec import SdfBodyAnalyzeRequest
from .generated_sdf import builder, robot
import trollius
from trollius import From

import pygazebo
import pygazebo.msg.joint_cmd_pb2


model = builder.get_sdf_model(robot)
sdf = SDF()
sdf.add_element(model)

@trollius.coroutine
def publish_loop():
    manager = yield From(pygazebo.connect())

    publisher = yield From(
        manager.advertise('/gazebo/default/analyze_body/request',
                          'revolve.msgs.SdfBodyAnalyzeRequest'))

    message = SdfBodyAnalyzeRequest()
    message.sdf = str(sdf)
    counter = 1

    while True:
        message.id = "request_%d" % counter
        counter += 1
        yield From(publisher.publish(message))
        yield From(trollius.sleep(0.1))

loop = trollius.get_event_loop()
loop.run_until_complete(publish_loop())