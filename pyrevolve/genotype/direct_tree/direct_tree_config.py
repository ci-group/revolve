
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
                 mutation_p_delete_subtree: float = 0.05,
                 mutation_p_generate_subtree: float = 0.05,
                 mutation_p_swap_subtree: float = 0.05,
                 mutation_p_mutate_oscillators: float = 0.05,
                 mutation_p_mutate_oscillator: float = 0.05,
                 mutate_oscillator_amplitude_sigma: float = 0.1,
                 mutate_oscillator_period_sigma: float = 0.1,
                 mutate_oscillator_phase_sigma: float = 0.1,
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
            p_delete_subtree=mutation_p_delete_subtree,
            p_generate_subtree=mutation_p_generate_subtree,
            p_swap_subtree=mutation_p_swap_subtree,
            p_mutate_oscillators=mutation_p_mutate_oscillators,
            p_mutate_oscillator=mutation_p_mutate_oscillator,
            mutate_oscillator_amplitude_sigma=mutate_oscillator_amplitude_sigma,
            mutate_oscillator_period_sigma=mutate_oscillator_period_sigma,
            mutate_oscillator_phase_sigma=mutate_oscillator_phase_sigma,
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
                 p_generate_subtree,
                 p_swap_subtree,
                 p_duplicate_subtree,
                 p_mutate_oscillators,
                 p_mutate_oscillator,
                 mutate_oscillator_amplitude_sigma,
                 mutate_oscillator_period_sigma,
                 mutate_oscillator_phase_sigma,
                 ):
        self.p_generate_subtree: float = p_generate_subtree
        self.p_duplicate_subtree: float = p_duplicate_subtree
        self.p_delete_subtree: float = p_delete_subtree
        self.p_swap_subtree: float = p_swap_subtree
        # global probability if to mutate oscillators at all
        self.p_mutate_oscillators: float = p_mutate_oscillators
        # probability tested for each single oscillator
        self.p_mutate_oscillator: float = p_mutate_oscillator
        # how much variance to mutate each of the oscillator parameters
        self.mutate_oscillator_amplitude_sigma: float = mutate_oscillator_amplitude_sigma
        self.mutate_oscillator_period_sigma: float = mutate_oscillator_period_sigma
        self.mutate_oscillator_phase_sigma: float = mutate_oscillator_phase_sigma
