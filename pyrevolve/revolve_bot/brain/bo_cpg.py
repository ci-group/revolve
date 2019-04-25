import xml.etree.ElementTree
from pyrevolve import SDF
from .base import Brain
import numpy as np

class BrainCPGBO(Brain):
    TYPE = 'bo-cpg'

    def __init__(self):
        # If you load a brain, set the top two to zero.
        self.n_init_samples = 25
        self.n_learning_iterations = 60
        self.n_cooldown_iterations = 0
        self.evaluation_rate = 50

        # CPG Hyperparameters to tune
        self.abs_output_bound = 1.0
        self.signal_factor = 1.5
        self.range_lb = -1.0
        self.range_ub = 1.0
        self.init_neuron_state = 0.5

        # BO hyper-parameters
        self.init_method = "LHS"  # {RS, LHS}

        # Automatically construct plots
        self.run_analytics = "true"

        # Supply existing brain to be validated. Empty string means train a new brain
        self.load_brain = ""
        # Various
        self.reset_robot_position = "false"
        self.reset_neuron_state_bool = "true"
        self.reset_neuron_random = "false"

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
            'reset_neuron_state_bool': str(self.reset_neuron_state_bool),
            'reset_neuron_random': str(self.reset_neuron_random),
            'load_brain': self.load_brain,
            'run_analytics': str(self.run_analytics),
            'init_neuron_state': str(self.init_neuron_state),
        })
