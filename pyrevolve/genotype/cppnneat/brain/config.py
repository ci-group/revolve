from dataclasses import dataclass

from ..config import Config as CppnneatConfig


@dataclass
class Config(CppnneatConfig):
    abs_output_bound: float  # clamp actuator position between this and -1 this. if you don't use, use 1.0
    use_frame_of_reference: bool  # enable gongjin steering
    output_signal_factor: float  # actuator gain. if you don't know, use 1.0
    range_ub: float  # scale weights to be between this and -this.  if you don't know, use 1.0
    init_neuron_state: float  # initial value of neurons. if you don't know, use 1/2*sqrt(2)
    reset_neuron_random: bool  # ignore init neuron state and use random value
