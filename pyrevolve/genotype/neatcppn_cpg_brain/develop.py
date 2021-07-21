from pyrevolve.genotype.neatcppn_cpg_brain.config import NeatcppnCpgBrainConfig
from pyrevolve.revolve_bot.brain import Brain
from pyrevolve.revolve_bot.brain.cpg import BrainCPG


def neatcppn_cpg_brain_develop(self, config: NeatcppnCpgBrainConfig) -> Brain:
    brain = BrainCPG()
    brain.abs_output_bound = config.abs_output_bound
    brain.use_frame_of_reference = config.use_frame_of_reference
    brain.signal_factor_all = config.signal_factor_all
    brain.signal_factor_mid = config.signal_factor_mid
    brain.signal_factor_left_right = config.signal_factor_left_right
    brain.range_lb = config.range_lb
    brain.range_ub = config.range_ub
    brain.init_neuron_state = config.init_neuron_state
    brain.load_brain = config.load_brain
    brain.output_directory = config.output_directory
    brain.run_analytics = config.run_analytics
    brain.reset_robot_position = config.reset_robot_position
    brain.reset_neuron_state_bool = config.reset_neuron_state_bool
    brain.reset_neuron_random = config.reset_neuron_random
    brain.verbose = config.verbose
    brain.startup_time = config.startup_time

    brain.weights = []  # TODO weights

    return brain
