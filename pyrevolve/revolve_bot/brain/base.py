import pyrevolve.revolve_bot.brain


class Brain(object):

    @staticmethod
    def from_yaml(yaml_brain):
        brain_type = yaml_brain['type']

        if brain_type == 'neural-network':
            return pyrevolve.revolve_bot.brain.BrainNN.from_yaml(yaml_brain)
        elif brain_type == 'rlpower-splines':
            return pyrevolve.revolve_bot.brain.BrainRLPowerSplines.from_yaml(yaml_brain)
        else:
            return Brain()

    def to_yaml(self):
        return {}

    def learner_sdf(self):
        return None

    def controller_sdf(self):
        return None
