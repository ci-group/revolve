from yaml_converter import YamlToProtobuf
from exception import RobotSpecificationException
from ..implementation import SpecImplementation


def yaml_to_protobuf(spec, yaml):
    """
    :param spec:
    :type spec: SpecImplementation
    :param yaml:
    :return:
    """
    obj = YamlToProtobuf(spec, yaml)
    return obj.get_protobuf()