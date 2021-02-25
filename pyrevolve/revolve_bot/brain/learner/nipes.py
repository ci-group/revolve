import xml.etree.ElementTree

from .base import Learner


class NIPESLearner(Learner):
    TYPE = 'nipes'

    def __init__(self):
        self.stagnation_length = 20
        self.elitist_restart = True
        self.CMAES_step = 1.0
        self.novelty_k_value = 15
        self.novelty_ratio = 1.
        self.novelty_decrement = 0.05
        self.novelty_threshold = 0.9
        self.novelty_archive_probability = 0.4
        self.population_stagnation_threshold = 0.05
        self.restart = True
        self.incremental_population = True

        self.verbose = False
        self.population_size = 10
        self.max_eval = 300

    @staticmethod
    def from_yaml(yaml_learner):
        LNIPES =  NIPESLearner()
        try:
            for key, value in yaml_learner.items():
                try:
                    setattr(LNIPES, key, value)
                except:
                    print(f"Couldn't set {key}, {value}")
        except:
            print("No NIPES")

        for key in vars(LNIPES):
            if getattr(LNIPES, key) is None:
                raise RuntimeError(f"Didn't load {LNIPES.TYPE} param {key}")

        return LNIPES

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'nipes',
            'stagnation_length': str(self.stagnation_length),
            'elitist_restart': str(self.elitist_restart),
            'CMAES_step': str(self.CMAES_step),
            'novelty_k_value': str(self.novelty_k_value),
            'novelty_ratio': str(self.novelty_ratio),
            'novelty_decrement': str(self.novelty_decrement),
            'novelty_threshold': str(self.novelty_threshold),
            'novelty_archive_probability': str(self.novelty_archive_probability),
            'population_stagnation_threshold': str(self.population_stagnation_threshold),
            'restart': str(self.restart),
            'incremental_population': str(self.incremental_population),

            'verbose': str(self.verbose),
            'population_size': str(self.population_size),
            'max_eval': str(self.max_eval),
        })
