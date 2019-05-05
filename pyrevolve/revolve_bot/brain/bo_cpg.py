"""
Note: Parameters are not set in this file. They are imported from the robot yaml-file, containing the
physical properties of the robot, as well as the brain (learner and controller) and the corresponding
parameters.
"""

import xml.etree.ElementTree
from .base import Brain
import time


class BrainCPGBO(Brain):
    TYPE = 'bo-cpg'

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

        # BO hyper-parameters
        self.init_method = None  # {RS, LHS}
        self.acquisition_function = None
        self.kernel_noise = None
        self.kernel_optimize_noise = None
        self.kernel_sigma_sq = None
        self.kernel_l = None
        self.kernel_squared_exp_ard_k = None
        self.acqui_gpucb_delta = None
        self.acqui_ucb_alpha = None
        self.acqui_ei_jitter = None
        self.n_init_samples = None

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

    @staticmethod
    def from_yaml(yaml_object):
        BCPGBO = BrainCPGBO()

        for my_type in ["controller", "learner", "meta"]:
            try:
                my_object = yaml_object[my_type]
                for key, value in my_object.items():
                    try:
                        setattr(BCPGBO, key, value)
                    except:
                        print("Couldn't set {}, {}", format(key, value))
            except:
                print("Didn't load {} parameters".format(my_type))

        return BCPGBO

    def to_yaml(self):
        return {
            'type': self.TYPE
        }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'bo',
            'robot_size': str(self.robot_size),
            'n_init_samples': str(self.n_init_samples),
            'n_learning_iterations': str(self.n_learning_iterations),
            'n_cooldown_iterations': str(self.n_cooldown_iterations),
            'evaluation_rate': str(self.evaluation_rate),
            'abs_output_bound': str(self.abs_output_bound),
            'init_method': self.init_method,
            'kernel_noise': str(self.kernel_noise),
            'kernel_optimize_noise': str(self.kernel_optimize_noise),
            'kernel_sigma_sq': str(self.kernel_sigma_sq),
            'kernel_l': str(self.kernel_l),
            'kernel_squared_exp_ard_k': str(self.kernel_squared_exp_ard_k),
            'acquisition_function': str(self.acquisition_function),
            'acqui_gpucb_delta': str(self.acqui_gpucb_delta),
            'acqui_ucb_alpha': str(self.acqui_ucb_alpha),
            'acqui_ei_jitter': str(self.acqui_ei_jitter),
        })

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {
            'type': 'cpg',
            'reset_robot_position': self.reset_robot_position,
            'reset_neuron_state_bool': str(self.reset_neuron_state_bool),
            'reset_neuron_random': str(self.reset_neuron_random),
            'load_brain': self.load_brain,
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
        })
