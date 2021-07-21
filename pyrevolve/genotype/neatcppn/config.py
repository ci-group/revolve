from typing import Any, Callable, Mapping

import multineat
from pyrevolve.genotype.neatcppn.genotype import NeatcppnGenotype
from pyrevolve.revolve_bot import RevolveBot


class NeatcppnGenotypeConfig:
    def __init__(
        self,
        n_inputs: int,
        n_outputs: int,
        develop_function: Callable[[object, int, multineat.Genome], RevolveBot],
        develop_userdata: object,
    ):
        self.multineat_params = self.generate_multineat_params()
        self._n_inputs = n_inputs
        self._n_outputs = n_outputs
        self._develop_function = develop_function
        self._develop_userdata = develop_userdata

        # TODO move
        self.cpg_settings = self.generate_brain_cpg_settings()

    @staticmethod
    def generate_multineat_params():
        params = multineat.Parameters()

        params.MutateRemLinkProb = 0.02
        params.RecurrentProb = 0.0
        params.OverallMutationRate = 0.15
        params.MutateAddLinkProb = 0.08
        params.MutateAddNeuronProb = 0.01
        params.MutateWeightsProb = 0.90
        params.MaxWeight = 8.0
        params.WeightMutationMaxPower = 0.2
        params.WeightReplacementMaxPower = 1.0
        params.MutateActivationAProb = 0.0
        params.ActivationAMutationMaxPower = 0.5
        params.MinActivationA = 0.05
        params.MaxActivationA = 6.0

        params.MutateNeuronActivationTypeProb = 0.03

        params.ActivationFunction_SignedSigmoid_Prob = 0.0
        params.ActivationFunction_UnsignedSigmoid_Prob = 0.0
        params.ActivationFunction_Tanh_Prob = 1.0
        params.ActivationFunction_TanhCubic_Prob = 0.0
        params.ActivationFunction_SignedStep_Prob = 1.0
        params.ActivationFunction_UnsignedStep_Prob = 0.0
        params.ActivationFunction_SignedGauss_Prob = 1.0
        params.ActivationFunction_UnsignedGauss_Prob = 0.0
        params.ActivationFunction_Abs_Prob = 0.0
        params.ActivationFunction_SignedSine_Prob = 1.0
        params.ActivationFunction_UnsignedSine_Prob = 0.0
        params.ActivationFunction_Linear_Prob = 1.0

        params.MutateNeuronTraitsProb = 0.0
        params.MutateLinkTraitsProb = 0.0

        params.AllowLoops = False

        return params

    @staticmethod
    def generate_brain_cpg_settings() -> Mapping[str, Any]:
        settings = {}

        # CPG hyper-parameters
        settings["abs_output_bound"] = 1.0
        settings["use_frame_of_reference"] = False
        settings["signal_factor_all"] = 4.0
        settings["signal_factor_mid"] = 2.5
        settings["signal_factor_left_right"] = 2.5
        settings["range_lb"] = None
        settings["range_ub"] = 1.0
        settings["init_neuron_state"] = 0.707

        # Various
        settings["load_brain"] = None
        settings["output_directory"] = None
        settings["run_analytics"] = None
        settings["reset_robot_position"] = None
        settings["reset_neuron_state_bool"] = None
        settings["reset_neuron_random"] = False
        settings["verbose"] = None
        settings["startup_time"] = None

        return settings
