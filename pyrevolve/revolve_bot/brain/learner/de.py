import xml.etree.ElementTree

from .base import Learner


class DELearner(Learner):
    TYPE = 'de'

    def __init__(self):
        self.subtype = None
        self.CR = 0.9
        self.F = 0.3
        self.n_parents = 3

        self.verbose = False
        self.population_size = 10
        self.max_eval = 300

    @staticmethod
    def from_yaml(yaml_learner):
        LDE =  DELearner()
        try:
            for key, value in yaml_learner.items():
                try:
                    setattr(LDE, key, value)
                except:
                    print(f"Couldn't set {key}, {value}")
        except:
            print("No DE")

        for key in vars(LDE):
            if getattr(LDE, key) is None:
                raise RuntimeError(f"Didn't load {LDE.TYPE} param {key}")

        return LDE

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'de',
            'subtype': str(self.subtype),
            'CR': str(self.CR),
            'F': str(self.F),
            'n_parents': str(self.n_parents),

            'verbose': str(self.verbose),
            'population_size': str(self.population_size),
            'max_eval': str(self.max_eval),
        })
