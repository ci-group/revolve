"""
"""
from __future__ import absolute_import
import yaml
from ..spec import BodyImplementation, NeuralNetImplementation
from ..spec.protobuf import *
from .decode import BodyDecoder, NeuralNetworkDecoder


def yaml_to_robot(body_spec, nn_spec, yaml):
    """
    :param body_spec:
    :type body_spec: BodyImplementation
    :param nn_spec:
    :type nn_spec: NeuralNetImplementation
    :param yaml:
    :type yaml: stream
    :return:
    """
    obj = YamlToRobot(body_spec, nn_spec)
    return obj.get_protobuf(yaml)


class YamlToRobot:
    """
    Sample converter creates a Robot protobuf message
    from a YAML stream and a body / neural net spec.
    """

    def __init__(self, body_spec, nn_spec):
        """
        :param body_spec:
        :type body_spec: BodyImplementation
        :return:
        """
        self.body_spec = body_spec
        self.nn_spec = nn_spec
        self.body_decoder = BodyDecoder(body_spec)
        self.brain_decoder = NeuralNetworkDecoder(nn_spec, body_spec)

    def get_protobuf(self, stream):
        """
        Returns a protobuf `Robot` for the given stream.

        :param stream:
        :type stream: stream
        :return:
        :rtype: Robot
        """
        obj = yaml.load(stream)

        robot = Robot()
        robot.id = obj.get('id', 0)
        robot.body.CopyFrom(self.body_decoder.decode(obj))
        robot.brain.CopyFrom(self.brain_decoder.decode(obj))
        return robot
