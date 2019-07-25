import xml.etree.ElementTree
from .base import Brain


class BrainRLPowerSplines(Brain):
    TYPE = 'rlpower-splines'

    def __init__(self, evaluation_rate=30.0):
        self._evaluation_rate = evaluation_rate

    @staticmethod
    def from_yaml(yaml_object):
        return BrainRLPowerSplines()

    def to_yaml(self):
        return {
            'type': self.TYPE
        }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'rlpower',
            'evaluation_rate': str(self._evaluation_rate),
        })

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {'type': 'spline'})
