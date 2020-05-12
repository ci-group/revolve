import xml.etree.ElementTree

from .base import Learner


class BOLearner(Learner):
    TYPE = 'bo'

    def __init__(self):
        self.n_init_samples = 1
        self.n_learning_iterations = 100
        self.evaluation_rate = 15.0
        self.init_method = 'LHS'
        self.kernel_noise = 0.00000001
        self.kernel_optimize_noise = False
        self.kernel_sigma_sq = 0.222
        self.kernel_l = 0.55
        self.kernel_squared_exp_ard_k = 4
        self.acqui_gpucb_delta = 0.5
        self.acqui_ucb_alpha = 0.44
        self.acqui_ei_jitter = 0.0
        self.acquisition_function = "UCB"

    @staticmethod
    def from_yaml(yaml_learner):
        # TODO read BO params
        return BOLearner()

    # def to_yaml(self):
    #     #TODO save BO params
    #     return {
    #         type: self.TYPE
    #     }

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'bo',
            'n_init_samples': str(self.n_init_samples),
            'n_learning_iterations': str(self.n_learning_iterations),
            'evaluation_rate': str(self.evaluation_rate),
            'init_method': str(self.init_method),
            'kernel_noise': str(self.kernel_noise),
            'kernel_optimize_noise': str(self.kernel_optimize_noise),
            'kernel_sigma_sq': str(self.kernel_sigma_sq),
            'kernel_l': str(self.kernel_l),
            'kernel_squared_exp_ard_k': str(self.kernel_squared_exp_ard_k),
            'acqui_gpucb_delta': str(self.acqui_gpucb_delta),
            'acqui_ucb_alpha': str(self.acqui_ucb_alpha),
            'acqui_ei_jitter': str(self.acqui_ei_jitter),
            'acquisition_function': str(self.acquisition_function),
        })
