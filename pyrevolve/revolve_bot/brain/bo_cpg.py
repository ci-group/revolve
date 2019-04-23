import xml.etree.ElementTree
from pyrevolve import SDF
from .base import Brain


class BrainCPGBO(Brain):
    TYPE = 'bo-cpg'

    def __init__(self):
        # Hard-code parameters here for now
        self.n_init_samples = 20
        self.n_learning_iterations = 5
        self.n_cooldown_iterations = 10
        self.evaluation_rate = 30.0

        # Bound for output signal
        self.abs_output_bound = 1.0
        self.signal_factor = 2.5

        # Weight ranges
        self.range_lb = -1
        self.range_ub = 1

        # BO hyper-parameters
        self.init_method = "LHS"  # {RS, LHS, ORT}

        # Automatically construct plots
        self.run_analytics = "true"

        # Supply existing brain to be validated. Empty string means train a new brain
        self.load_brain = ""

        # Various
        self.reset_robot_position = "true"
        self.reset_neuron_state_valid = "true"

    @staticmethod
    def from_yaml(yaml_object):
        return BrainCPGBO()

    def to_yaml(self):
        return {
            'type': self.TYPE
        }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'bo',
            'n_init_samples': str(self.n_init_samples),
            'n_learning_iterations': str(self.n_learning_iterations),
            'n_cooldown_iterations': str(self.n_cooldown_iterations),
            'evaluation_rate': str(self.evaluation_rate),
            'abs_output_bound': str(self.abs_output_bound),
            'signal_factor': str(self.signal_factor),
            'range_lb': str(self.range_lb),
            'range_ub': str(self.range_ub),
            'init_method': self.init_method,
        })

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {
            'type': 'cpg',
            'reset_robot_position': self.reset_robot_position,
            'reset_neuron_state_valid': str(self.reset_neuron_state_valid),
            'load_brain': self.load_brain,
            'run_analytics': str(self.run_analytics),
        })
