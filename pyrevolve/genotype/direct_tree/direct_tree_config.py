
class DirectTreeGenotypeConfig(object):
    def __init__(self,
                 max_parts: int = 50,
                 min_parts: int = 10,
                 max_oscillation: float = 5,
                 init_n_parts_mu: float = 10,
                 init_n_parts_sigma: float = 4,
                 init_prob_no_child: float = 0.1,
                 init_prob_child_active_joint: float = 0.4,
                 init_prob_child_block: float = 0.5,
                 mutation_p_duplicate_subtree: float = 0.05,
                 mutation_p_swap_subtree: float = 0.05,
                 mutation_p_delete_subtree: float = 0.05,
                 ):
        self.max_parts: int = max_parts
        self.min_parts: int = min_parts
        self.max_oscillation: float = max_oscillation
        
        self.init: RandomGenerateConfig = RandomGenerateConfig(
            n_parts_mu=init_n_parts_mu,
            n_parts_sigma=init_n_parts_sigma,
            prob_no_child=init_prob_no_child,
            prob_child_active_joint=init_prob_child_active_joint,
            prob_child_block=init_prob_child_block,
        )

        self.mutation: DirectTreeMutationConfig = DirectTreeMutationConfig(
            p_duplicate_subtree=mutation_p_duplicate_subtree,
            p_swap_subtree=mutation_p_swap_subtree,
            p_delete_subtree=mutation_p_delete_subtree,
        )


class RandomGenerateConfig:
    def __init__(self,
                 n_parts_mu: float,
                 n_parts_sigma: float,
                 prob_no_child: float,
                 prob_child_active_joint: float,
                 prob_child_block: float,
                 ):
        self.n_parts_mu: float = n_parts_mu
        self.n_parts_sigma: float = n_parts_sigma
        self.prob_no_child: float = prob_no_child
        self.prob_child_active_joint: float = prob_child_active_joint
        self.prob_child_block: float = prob_child_block


class DirectTreeMutationConfig:
    def __init__(self,
                 p_delete_subtree,
                 p_swap_subtree,
                 p_duplicate_subtree):
        self.p_duplicate_subtree: float = p_duplicate_subtree
        self.p_swap_subtree: float = p_swap_subtree
        self.p_delete_subtree: float = p_delete_subtree
