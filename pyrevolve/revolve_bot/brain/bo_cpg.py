import xml.etree.ElementTree
from .base import Brain
import time


class BrainCPGBO(Brain):
    TYPE = 'bo-cpg'

    def __init__(self):
        # CPG hyper-parameters
        self.abs_output_bound = 1.0
        self.signal_factor = 1.5
        self.range_lb = -1.0
        self.range_ub = 1.0
        self.init_neuron_state = 0.5

        # BO hyper-parameters
        self.init_method = ""  # {RS, LHS}
        self.acquisition_function = ""
        self.kernel_noise = ""
        self.kernel_optimize_noise = ""
        self.kernel_sigma_sq = ""
        self.kernel_l = ""
        self.kernel_squared_exp_ard_k = ""
        self.acqui_gpucb_delta = ""
        self.acqui_ucb_alpha = ""
        self.acqui_ei_jitter = ""
        self.n_init_samples = ""

        # Various
        self.n_learning_iterations = 10
        self.n_cooldown_iterations = 0
        self.load_brain = ""
        self.output_directory = ""
        self.run_analytics = "true"
        self.reset_robot_position = "true"
        self.reset_neuron_state_bool = "true"
        self.reset_neuron_random = "false"
        self.verbose = 1
        self.startup_time = 0
        self.evaluation_rate = 50

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
            'run_analytics': str(self.run_analytics),
            'init_neuron_state': str(self.init_neuron_state),
            'output_directory': str(self.output_directory),
            'verbose': str(self.verbose),
            'range_lb': str(self.range_lb),
            'range_ub': str(self.range_ub),
            'signal_factor': str(self.signal_factor),
            'startup_time': str(self.startup_time),
        })
