"""
Note: Parameters are not set in this file. They are imported from the robot yaml-file, containing the
physical properties of the robot, as well as the brain (learner and controller) and the corresponding
parameters.
"""

import xml.etree.ElementTree
from .base import Brain


class BrainCPG(Brain):
    TYPE = 'cpg'

    def __init__(self):
        # CPG hyper-parameters
        self.abs_output_bound = None
        self.use_frame_of_reference = "false"
        self.signal_factor_all = ""
        self.signal_factor_mid = None
        self.signal_factor_left_right = None
        self.range_lb = None
        self.range_ub = None
        self.init_neuron_state = None
        # Various
        self.robot_size = None
        self.n_learning_iterations = None
        self.n_cooldown_iterations = None
        self.load_brain = None
        self.output_directory = None
        self.run_analytics = None
        self.reset_robot_position = None
        self.reset_neuron_state_bool = None
        self.reset_neuron_random = None
        self.verbose = None
        self.startup_time = None
        self.evaluation_rate = None
        self.weights = []

    @staticmethod
    def from_yaml(yaml_object):
        BCPG = BrainCPG()
        try:
            my_object = yaml_object["controller"]
            for key, value in my_object.items():
                try:
                    setattr(BCPG, key, value)
                except:
                    print(f"Couldn't set {key}, {value}")
        except:
            print("Didn't load \"controller\" parameters")

        return BCPG

    def to_yaml(self):
        return {
            'type': self.TYPE,
            'controller': {
                'abs_output_bound': self.abs_output_bound,
                'reset_robot_position': self.reset_robot_position,
                'reset_neuron_state_bool': self.reset_neuron_state_bool,
                'reset_neuron_random': self.reset_neuron_random,
                'load_brain': self.load_brain,
                'use_frame_of_reference': self.use_frame_of_reference,
                'run_analytics': self.run_analytics,
                'init_neuron_state': self.init_neuron_state,
                'output_directory': self.output_directory,
                'verbose': self.verbose,
                'range_lb': self.range_lb,
                'range_ub': self.range_ub,
                'signal_factor_all': self.signal_factor_all,
                'signal_factor_mid': self.signal_factor_mid,
                'signal_factor_left_right': self.signal_factor_left_right,
                'startup_time': self.startup_time,
                'weights': self.weights,
            }
        }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'offline',
        })

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {
            'type': 'cpg',
            'abs_output_bound': str(self.abs_output_bound),
            'reset_robot_position': str(self.reset_robot_position),
            'reset_neuron_state_bool': str(self.reset_neuron_state_bool),
            'reset_neuron_random': str(self.reset_neuron_random),
            'load_brain': str(self.load_brain),
            'use_frame_of_reference': str(self.use_frame_of_reference),
            'run_analytics': str(self.run_analytics),
            'init_neuron_state': str(self.init_neuron_state),
            'output_directory': str(self.output_directory),
            'verbose': str(self.verbose),
            'range_lb': str(self.range_lb),
            'range_ub': str(self.range_ub),
            'signal_factor_all': str(self.signal_factor_all),
            'signal_factor_mid': str(self.signal_factor_mid),
            'signal_factor_left_right': str(self.signal_factor_left_right),
            'startup_time': str(self.startup_time),
            'weights': ';'.join(str(x) for x in self.weights)
        })
