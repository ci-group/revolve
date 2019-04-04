import xml.etree.ElementTree
from .base import Brain


class BrainRLPowerSplines(Brain):
    TYPE = 'rlpower-splines'

    @staticmethod
    def from_yaml(yaml_object):
        return BrainRLPowerSplines()

    def to_yaml(self):
        return {
            'type': self.TYPE
        }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {'type': 'rlpower'})

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {'type': 'spline'})
