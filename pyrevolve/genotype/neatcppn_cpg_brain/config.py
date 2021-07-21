from dataclasses import dataclass


@dataclass
class NeatcppnCpgBrainConfig:
    abs_output_bound: float
    use_frame_of_reference: bool
    signal_factor_all: float
    signal_factor_mid: float
    signal_factor_left_right: float
    range_lb: float
    range_ub: float
    init_neuron_state: float

    load_brain: bool  # not sure if type correct
    output_directory: str  # not sure if type correct
    run_analytics: bool  # not sure if type correct
    reset_robot_position: bool  # not sure if type correct
    reset_neuron_state_bool: bool  # not sure if type correct
    reset_neuron_random: bool
    verbose: bool  # not sure if type correct
    startup_time: float  # not sure if type correct
