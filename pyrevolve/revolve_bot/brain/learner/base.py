import xml.etree.ElementTree
import pyrevolve.revolve_bot.brain.learner as learners


class Learner(object):
    TYPE = 'offline'

    @staticmethod
    def from_yaml(yaml_learner):
        brain_type = yaml_learner['type']

        if brain_type == learners.bo.BOLearner.TYPE:
            return learners.bo.BOLearner.from_yaml(yaml_learner)
        else:
            print("No matching brain type defined in yaml file.")
            return Learner()

    def to_yaml(self):
        return {
            'type': self.TYPE
        }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'offline',
        })
