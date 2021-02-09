
class DirectTreeGenomeConfig(object):
    def __init__(self):
        self.init: RandomGenerateConfig = RandomGenerateConfig()
        self.max_parts: int = 50
        self.max_oscillation: float = 5


class RandomGenerateConfig:
    def __init__(self):
        self.n_parts_mu: float = 10
        self.n_parts_sigma: float = 4
        self.prob_no_child: float = 0.1
        self.prob_child_active_joint: float = 0.4
        self.prob_child_block: float = 0.5


class DirectTreeMutationConfig:
    def __init__(self):
        pass

