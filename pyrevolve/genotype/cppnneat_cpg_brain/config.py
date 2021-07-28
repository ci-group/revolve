from dataclasses import dataclass

import multineat


@dataclass
class CppnneatCpgBrainConfig:
    multineat_params: multineat.Parameters
    innov_db: multineat.InnovationDatabase
    rng: multineat.RNG

    abs_output_bound: float
    use_frame_of_reference: bool
    signal_factor_all: float
    signal_factor_mid: float
    signal_factor_left_right: float
    range_ub: float
    init_neuron_state: float  # initial value of neurons
    reset_neuron_random: bool  # ignore init neuron state and use random value
