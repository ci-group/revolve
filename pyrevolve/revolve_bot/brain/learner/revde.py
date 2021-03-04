import xml

from pyrevolve.revolve_bot.brain.learner import Learner


class RevDELearner(Learner):
    TYPE = 'de'

    def __init__(self):
        self.subtype = "revde"
        self.CR = 0.9
        self.F = 0.5
        self.n_parents = 3
        self.verbose = "false"
        self.population_size = 20
        self.max_eval = 100

    def to_yaml(self):
        return {
            'type': self.TYPE,
            'subtype': self.subtype,
            'CR': self.CR,
            'F': self.F,
            'n_parents': self.n_parents,
            'verbose': self.verbose,
            'population_size': self.population_size,
            'max_eval': self.max_eval,
        }

    @staticmethod
    def from_yaml(yaml_object):
        revde = RevDELearner()
        for yaml_params in ["type", "subtype", "CR", "F", "n_parents", "verbose", "population_size", "max_eval"]:
            try:
                for key, value in yaml_object.items():
                    try:
                        setattr(revde, key, value)
                    except:
                        print("Couldn't set {}, {}", format(key, value))
            except:
                print("Didn't load {} parameters".format(yaml_params))

        return revde


    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': self.TYPE,
            'subtype': str(self.subtype),
            'CR': str(self.CR),
            'F': str(self.F),
            'n_parents': str(self.n_parents),
            'verbose': str(self.verbose),
            'population_size': str(self.population_size),
            'max_eval': str(self.max_eval),
        })

