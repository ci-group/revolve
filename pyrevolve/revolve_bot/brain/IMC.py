"""
Note: Parameters are not set in this file. They are imported from the robot yaml-file, containing the
physical properties of the robot, as well as the brain (learner and controller) and the corresponding
parameters.
"""

import xml.etree.ElementTree
from .base import Brain


class BrainIMC(Brain):

    def __init__(self):
        # CPG hyper-parameters
        self.active = "true"
        self.restore_checkpoint = "true"
        self.save_checkpoint = "true"
        self.learning_rate = None
        self.beta1 = None
        self.beta2 = None
        self.weight_decay = None

    @staticmethod
    def from_yaml(yaml_object):
        BIMC = BrainIMC()
        try:
            for key, value in yaml_object.items():
                try:
                    setattr(BIMC, key, value)
                except:
                    print(f"Couldn't set {key}, {value}")
        except:
            print("No IMC")
        return BIMC

    def to_yaml(self):
        return {
            'IMC': {
                'active': self.active,
                'restore_checkpoint': self.restore_checkpoint,
                'save_checkpoint': self.save_checkpoint,
                'learning_rate': self.learning_rate,
                'beta1': self.beta1,
                'beta2': self.beta2,
                'weight_decay': self.weight_decay
            }
        }

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:IMC', {
            'active': str(self.active),
            'restore_checkpoint': str(self.restore_checkpoint),
            'save_checkpoint': str(self.save_checkpoint),
            'learning_rate': str(self.learning_rate),
            'beta1': str(self.beta1),
            'beta2': str(self.beta2),
            'weight_decay': str(self.weight_decay)
        })
