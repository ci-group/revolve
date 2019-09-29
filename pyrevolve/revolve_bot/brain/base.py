import pyrevolve.revolve_bot.brain


class Brain(object):

    @staticmethod
    def from_yaml(yaml_brain):
        brain_type = yaml_brain['type']

        if brain_type == pyrevolve.revolve_bot.brain.BrainNN.TYPE:
            return pyrevolve.revolve_bot.brain.BrainNN.from_yaml(yaml_brain)
        elif brain_type == pyrevolve.revolve_bot.brain.BrainRLPowerSplines.TYPE:
            return pyrevolve.revolve_bot.brain.BrainRLPowerSplines.from_yaml(yaml_brain)
        elif brain_type == pyrevolve.revolve_bot.brain.BrainCPGBO.TYPE:
            return pyrevolve.revolve_bot.brain.BrainCPGBO.from_yaml(yaml_brain)
        elif brain_type == pyrevolve.revolve_bot.brain.BrainCPG.TYPE:
            return pyrevolve.revolve_bot.brain.BrainCPG.from_yaml(yaml_brain)
        else:
            print("No matching brain type defined in yaml file.")
            return Brain()

    def to_yaml(self):
        return {}

    def learner_sdf(self):
        return None

    def controller_sdf(self):
        return None
