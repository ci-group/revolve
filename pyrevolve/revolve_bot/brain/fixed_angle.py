import xml.etree.ElementTree
from pyrevolve.revolve_bot.brain import Brain


class FixedAngleBrain(Brain):
    TYPE = 'fixed-angle'

    def __init__(self, angle: float):
        self._angle = angle

    @staticmethod
    def from_yaml(yaml_object):
        return FixedAngleBrain(float(yaml_object['angle']))

    def to_yaml(self):
        return {
            'type': self.TYPE
        }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {'type': 'offline'})

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {
            'type': 'fixed-angle',
            'angle': str(self._angle),
        })
