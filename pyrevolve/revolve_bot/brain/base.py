from pyrevolve.revolve_bot import brain as brains
from pyrevolve.revolve_bot.brain.learner import Learner


class Brain(object):
    TYPE = 'NONE'

    def __init__(self):
        self.learner = None

    @staticmethod
    def from_yaml(yaml_brain):
        brain_type = yaml_brain['type']

        brain = None
        if brain_type == brains.BrainNN.TYPE:
            brain = brains.BrainNN.from_yaml(yaml_brain)
        elif brain_type == brains.BrainRLPowerSplines.TYPE:
            brain = brains.BrainRLPowerSplines.from_yaml(yaml_brain)
        elif brain_type == brains.BrainCPGBO.TYPE:
            brain = brains.BrainCPGBO.from_yaml(yaml_brain)
        elif brain_type == brains.BrainCPG.TYPE:
            brain = brains.BrainCPG.from_yaml(yaml_brain)
        elif brain_type == brains.BrainCPPNCPG.TYPE:
            brain = brains.BrainCPPNCPG.from_yaml(yaml_brain)
        else:
            print("No matching brain type defined in yaml file.")
            brain = Brain()

        brain.learner = Learner.from_yaml(yaml_brain['learner'])
        if 'IMC' in yaml_brain:
            brain.IMC = brains.BrainIMC.from_yaml(yaml_brain['IMC'])
        return brain

    def to_yaml(self):
        return {
            'type': self.TYPE,
            'learner': self.learner.to_yaml()
        }

    def learner_sdf(self):
        return self.learner.learner_sdf()

    def controller_sdf(self):
        return None
