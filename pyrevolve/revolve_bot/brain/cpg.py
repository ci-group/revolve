"""
Note: Parameters are not set in this file. They are imported from the robot yaml-file, containing the
physical properties of the robot, as well as the brain (learner and controller) and the corresponding
parameters.
"""

import xml.etree.ElementTree
from typing import Dict, List

from .base import Brain
from .learner import RevDELearner


class BrainIMC:

    def __init__(self):
        self.active = "false"
        self.learning_rate = 0.05
        self.beta1 = 0.9
        self.beta2 = 0.99
        self.weight_decay = 0.001
        self.window_length = 30
        self.restore_checkpoint = "false"
        self.save_checkpoint = "false"

    @staticmethod
    def from_yaml(yaml_object):
        imc = BrainIMC()
        for yaml_params in ["active", "learning_rate", "beta1", "beta2", "weight_decay", "window_length", "restore_checkpoint", "save_checkpoint"]:
            try:
                for key, value in yaml_object.items():
                    try:
                        setattr(imc, key, value)
                    except:
                        print("Couldn't set {}, {}", format(key, value))
            except:
                print("Didn't load {} parameters".format(yaml_params))

        return imc

    def to_yaml(self):
        return {
            'active': self.active,
            'learning_rate': self.learning_rate,
            'beta1': self.beta1,
            'beta2': self.beta2,
            'weight_decay': self.weight_decay,
            'window_length': self.window_length,
            'restore_checkpoint': self.restore_checkpoint,
            'save_checkpoint': self.save_checkpoint,
        }


class BrainCPGMeta:

    def __init__(self, size: int):
        self.robot_size = size
        self.run_analytics = "true"
        self.n_learning_iterations = 10
        self.n_cooldown_iterations = 1
        self.reset_robot_position = "false"
        self.evaluation_rate = 30
        self.output_directory = ""  # /home/admin/output_learners
        self.verbose = 0
        self.startup_time = 0

    @staticmethod
    def from_yaml(yaml_object):
        meta = BrainCPGMeta(0)
        for yaml_params in ["robot_size", "run_analytics", "n_learning_iterations", "n_cooldown_iterations", "reset_robot_position", "evaluation_rate", "output_directory", "verbose", "startup_time"]:
            try:
                for key, value in yaml_object.items():
                    try:
                        setattr(meta, key, value)
                    except:
                        print("Couldn't set {}, {}", format(key, value))
            except:
                print("Didn't load {} parameters".format(yaml_params))

        return meta

    def to_yaml(self):
        return {
            'robot_size': self.robot_size,
            'run_analytics': self.run_analytics,
            'n_learning_iterations': self.n_learning_iterations,
            'n_cooldown_iterations': self.n_cooldown_iterations,
            'reset_robot_position': self.reset_robot_position,
            'evaluation_rate': self.evaluation_rate,
            'output_directory': self.output_directory,
            'verbose': self.verbose,
            'startup_time': self.startup_time,
        }


class BrainCPGController:

    def __init__(self, weights):
        # CPG hyper-parameters
        self.reset_neuron_random = "false"
        self.use_frame_of_reference = "false"

        self.signal_factor_all = 1.0
        self.signal_factor_mid = 1.0
        self.signal_factor_left_right = 1.0
        self.abs_output_bound = 1.0

        self.range_ub = 1.0
        self.init_neuron_state = 0.707
        self.weights = weights

    @staticmethod
    def from_yaml(yaml_object):
        controller = BrainCPGController([])
        for yaml_params in ["reset_neuron_random", "use_frame_of_reference", "signal_factor_all", "signal_factor_mid", "signal_factor_left_right", "abs_output_bound", "range_ub", "init_neuron_state", "weights"]:
            try:
                for key, value in yaml_object.items():
                    try:
                        setattr(controller, key, value)
                    except:
                        print("Couldn't set {}, {}", format(key, value))
            except:
                print("Didn't load {} parameters".format(yaml_params))

        return controller

    def to_yaml(self):
        return {
            'reset_neuron_random': self.reset_neuron_random,
            'use_frame_of_reference': self.use_frame_of_reference,
            'signal_factor_all': self.signal_factor_all,
            'signal_factor_mid': self.signal_factor_mid,
            'signal_factor_left_right': self.signal_factor_left_right,
            'abs_output_bound': self.abs_output_bound,
            'init_neuron_state': self.init_neuron_state,
            'range_ub': self.range_ub,
            'weights': self.weights,
        }


class BrainCPG(Brain):
    TYPE = 'cpg'

    def __init__(self, revolve_bot):

        super().__init__()

        # Various
        self.range_lb = 0.0
        self.load_brain = None
        self.reset_neuron_state_bool = None
        self.reset_neuron_random = None

        if revolve_bot is None:
            return

        size = self._count_modules(revolve_bot.body)
        weights = self._get_neural_weights(revolve_bot._brain)
        self.meta = BrainCPGMeta(size)
        self.controller = BrainCPGController(weights)
        self.learner = RevDELearner()
        self.imc = BrainIMC()

    def _get_neural_weights(self, brain):
        weights = []
        for node in brain.params.keys():
            weights.append(brain.params[node].amplitude)
        return weights

    def _count_modules(self, body, count = 0):
        if body.children is None:
            return count + 1

        if isinstance(body.children, List):
            for child in body.children:
                if child is None:
                    continue
                count = self._count_modules(child, count)

        if isinstance(body.children, Dict):
            for key in body.children.keys():
                child = body.children[key]
                if child is None:
                    continue
                count = self._count_modules(child, count)

        return count + 1

    @staticmethod
    def from_yaml(yaml_object):
        CPG = BrainCPG(None)

        for my_type in ["controller", "learner", "meta", "IMC"]:
            try:
                my_object = yaml_object[my_type]
                if my_type == "meta":
                    CPG.meta = BrainCPGMeta.from_yaml(my_object)
                elif my_type == "learner":
                    CPG.learner = RevDELearner.from_yaml(my_object)
                elif my_type == "controller":
                    CPG.controller = BrainCPGController.from_yaml(my_object)
                elif my_type == "IMC":
                    CPG.imc = BrainIMC.from_yaml(my_object)
            except:
                print("Didn't load {} parameters".format(my_type))

        return CPG

    def to_yaml(self):
        return {
            'controller': self.controller.to_yaml(),
            'meta': self.meta.to_yaml(),
            'learner': self.learner.to_yaml(),
            'IMC': self.imc.to_yaml(),
            'type': self.TYPE,
        }

    def controller_sdf(self):
        return xml.etree.ElementTree.Element('rv:controller', {
            'type': 'cpg',
            'abs_output_bound': str(self.controller.abs_output_bound),
            'reset_robot_position': str(self.meta.reset_robot_position),
            'reset_neuron_state_bool': str(self.reset_neuron_state_bool),
            'reset_neuron_random': str(self.reset_neuron_random),
            'load_brain': str(self.load_brain),
            'use_frame_of_reference': str(self.controller.use_frame_of_reference),
            'run_analytics': str(self.meta.run_analytics),
            'init_neuron_state': str(self.controller.init_neuron_state),
            'output_directory': str(self.meta.output_directory),
            'verbose': str(self.meta.verbose),
            'n_learning_iterations': str(self.meta.n_learning_iterations),
            'evaluation_rate': str(self.meta.evaluation_rate),
            'range_lb': str(self.range_lb),
            'range_ub': str(self.controller.range_ub),
            'signal_factor_all': str(self.controller.signal_factor_all),
            'signal_factor_mid': str(self.controller.signal_factor_mid),
            'signal_factor_left_right': str(self.controller.signal_factor_left_right),
            'startup_time': str(self.meta.startup_time),
            'weights': ';'.join(str(x) for x in self.controller.weights)
        })
