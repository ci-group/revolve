import xml.etree.ElementTree
from pyrevolve.revolve_bot.brain import learner as learners


class Learner(object):
    TYPE = 'offline'

    @staticmethod
    def from_yaml(yaml_learner):
        brain_type = yaml_learner['type']

        if brain_type == learners.bo.BOLearner.TYPE:
            return learners.bo.BOLearner.from_yaml(yaml_learner)
        if brain_type == learners.hyperneat.HyperNEATLearner.TYPE:
            return learners.hyperneat.HyperNEATLearner.from_yaml(yaml_learner)
        if brain_type == learners.nipes.NIPESLearner.TYPE:
            return learners.nipes.NIPESLearner.from_yaml(yaml_learner)
        if brain_type == learners.de.DELearner.TYPE:
            return learners.de.DELearner.from_yaml(yaml_learner)
        else:
            print("No matching brain/learner type defined in yaml file.")
            return Learner()

    def to_yaml(self):
        return {
            'type': self.TYPE
        }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'offline',
        })
