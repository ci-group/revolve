"""
"""
from __future__ import absolute_import
import yaml
from ..spec import BodyImplementation, NeuralNetImplementation
from ..spec.msgs import *
from .decode import BodyDecoder, NeuralNetworkDecoder
from .proto_to_yaml import BodyEncoder, NeuralNetworkEncoder

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
    
def robot_to_yaml(body_spec, nn_spec, bot_pb):
    """
    :param body_spec:
    :type body_spec: BodyImplementation
    :param nn_spec:
    :type nn_spec: NeuralNetImplementation
    :param bot_pb:
    :type bot_pb: protobuf robot object
    :return:
    :rtype: stream
    """
    obj = RobotToYaml(body_spec, nn_spec)
    return obj.get_yaml(bot_pb)

def unicode_representer(dumper, data):
        return dumper.represent_scalar(u'tag:yaml.org,2002:str', data)


class YamlToRobot:
    """
    Sample converter creates a Robot protobuf message
    from a YAML stream and a body / neural net spec.
    """

    def __init__(self, body_spec, nn_spec):
        """
        :param body_spec:
        :type body_spec: BodyImplementation
        :param nn_spec:
        :type nn_spec: NeuralNetImplementation
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


class RobotToYaml:
    """
    Sample converter creates a YAML stream from a 
    Robot protobuf message and a body / neural net spec.
    """

    def __init__(self, body_spec, nn_spec):
        """
        ::param body_spec:
        :type body_spec: BodyImplementation
        :param nn_spec:
        :type nn_spec: NeuralNetImplementation
        """
        self.body_spec = body_spec
        self.nn_spec = nn_spec
        self.body_encoder = BodyEncoder(body_spec)
        self.brain_encoder = NeuralNetworkEncoder(nn_spec)

    def get_yaml(self, bot_pb):
        """
        Converts a protobuf robot object into YAML file which it then returns
        :param bot_pb:
        :type bot_pb: Robot protobuf object
        :return:
        :rtype: YAML file
        """
        yaml.add_representer(unicode, unicode_representer)
        bot_yaml = {}

        id = bot_pb.id
        body = bot_pb.body
        brain = bot_pb.brain

        bot_yaml['id'] = id
        bot_yaml['body'] = self.body_encoder.parse_body(body.root)
        bot_yaml['brain'] = self.brain_encoder.parse_neural_network(brain)

        return yaml.dump(bot_yaml, default_flow_style=False)
