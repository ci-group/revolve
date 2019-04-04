import xml.etree.ElementTree
from .base import Brain


class BrainCPGBO(Brain):

    @staticmethod
    def from_yaml(yaml_object):
        return BrainCPGBO()

    def to_yaml(self):
        return {}

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {'type': 'bo'})

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {'type': 'cpg'})
