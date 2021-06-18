from __future__ import annotations

import enum
import multineat
import re
import sys

from pyrevolve.genotype import Genotype
from pyrevolve.revolve_bot.brain import BrainCPG, BrainCPPNCPG


class BrainType(enum.Enum):
    NN = 0
    CPPN = 1
    CPG = 2  # HyperNEAT -> CPG


class NeatBrainGenomeConfig:
    def __init__(self, brain_type: BrainType = BrainType.CPG, random_seed=None):
        self._brain_type = brain_type
        self.innov_db = multineat.InnovationDatabase()
        # TODO self.innov_db.Init_with_genome(a)
        self.rng = multineat.RNG()
        if random_seed is None:
            self.rng.TimeSeed()
        else:
            self.rng.Seed(random_seed)

        # normal NEAT section
        self.n_inputs = 1
        self.n_outputs = 1

        # generate multineat params object
        self.multineat_params = self._generate_multineat_params(brain_type)

        # CPG parameters
        self.reset_neuron_random = False
        self.use_frame_of_reference = False
        self.init_neuron_state = 0.707
        self.range_ub = 1.0
        self.signal_factor_all = 4.0
        self.signal_factor_mid = 2.5
        self.signal_factor_left_right = 2.5
        self.abs_output_bound = 1.0

    @property
    def brain_type(self):
        return self._brain_type

    @brain_type.setter
    def brain_type(self, brain_type: BrainType):
        self._brain_type = brain_type
        self._regenerate_multineat_params()

    def _regenerate_multineat_params(self):
        self.multineat_params = self._generate_multineat_params(self._brain_type)

    @staticmethod
    def _generate_multineat_params(brain_type: BrainType):
        params = multineat.Parameters()

        if brain_type is BrainType.CPG:
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
        elif brain_type is BrainType.NN:
            params.RecurrentProb = 0.0
            params.OverallMutationRate = 1.0

            params.ArchiveEnforcement = False

            params.MutateWeightsProb = 0.05

            params.WeightMutationMaxPower = 0.5
            params.WeightReplacementMaxPower = 8.0
            params.MutateWeightsSevereProb = 0.0
            params.WeightMutationRate = 0.25
            params.WeightReplacementRate = 0.9

            params.MaxWeight = 8.0

            params.MutateAddNeuronProb = 0.001
            params.MutateAddLinkProb = 0.3
            params.MutateRemLinkProb = 0.0

            params.MinActivationA = 4.9
            params.MaxActivationA = 4.9

            params.ActivationFunction_SignedSigmoid_Prob = 0.0
            params.ActivationFunction_UnsignedSigmoid_Prob = 1.0
            params.ActivationFunction_Tanh_Prob = 0.0
            params.ActivationFunction_SignedStep_Prob = 0.0

            params.MutateNeuronTraitsProb = 0.0
            params.MutateLinkTraitsProb = 0.0

            params.AllowLoops = True
            params.AllowClones = True

        else:
            raise NotImplementedError(f"{brain_type} not supported")

        return params

    def is_brain_cppn(self):
        return self.brain_type is BrainType.CPPN or self.brain_type is BrainType.CPG


class NeatBrainGenome(Genotype):
    def __init__(self, conf: NeatBrainGenomeConfig = None, robot_id=None):  # Change
        if conf is None:
            self._brain_type = None
            self._neat_genome = None
            return

        # self.id = int(robot_id)
        self._brain_type = conf.brain_type
        is_cppn = conf.is_brain_cppn()

        if is_cppn:

            # if HyperNEAT
            if conf.brain_type is BrainType.CPG:
                # calculate number of inputs
                n_coordinates = 4
                conf.n_inputs = n_coordinates * 2

                # calculate number of outputs
                conf.n_outputs = 1  # connection weight
                # conf.n_outputs += 1  # connection to output weight - unused now

            self._neat_genome = multineat.Genome(
                0,  # ID
                conf.n_inputs,
                0,  # n_hidden
                conf.n_outputs,
                False,  # FS_NEAT
                multineat.ActivationFunction.TANH,  # output activation type
                multineat.ActivationFunction.TANH,  # hidden activation type
                0,  # seed_type
                conf.multineat_params,
                0,  # number of hidden layers
            )
        else:
            self._neat_genome = multineat.Genome(
                0,  # ID
                conf.n_inputs,
                0,  # n_hidden
                conf.n_outputs,
                False,  # FS_NEAT
                multineat.ActivationFunction.UNSIGNED_SIGMOID,  # output activation type
                multineat.ActivationFunction.UNSIGNED_SIGMOID,  # hidden activation type
                0,  # seed_type
                conf.multineat_params,
                0,  # number of hidden layers
            )

        if type(robot_id) is int:
            self.id = robot_id
        else:
            self.id = int(re.search(r'\d+', str(robot_id))[0])
        self.phenotype = None

    def load_genotype(self, file_path: str):
        with open(file_path) as f:
            lines = f.readlines()
            self._load_genotype_from(lines[0])

    def _load_genotype_from(self, text):
        text = text.strip()
        self._neat_genome.Deserialize(text.replace('inf', str(sys.float_info.max)).strip('\n'))

    def export_genotype(self, file_path: str):
        with open(file_path, 'w+') as file:
            self._export_genotype_open_file(file)

    def _export_genotype_open_file(self, file):
        text = self._neat_genome.Serialize()
        file.write(text + '\n')

    # override
    def clone(self):
        clone = NeatBrainGenome()
        clone._brain_type = self._brain_type  # the conf must not be deep copied
        clone._neat_genome = multineat.Genome(self._neat_genome)
        return clone

    @property
    def id(self):
        return str(self._neat_genome.GetID())

    @id.setter
    def id(self, value: int):
        self._neat_genome.SetID(int(value))

    def develop(self):
        if self._brain_type is BrainType.CPG:
            # basically, HyperNEAT
            brain = BrainCPPNCPG(self._neat_genome)
            brain.reset_neuron_random = False
            brain.use_frame_of_reference = False
            brain.init_neuron_state = 0.707
            brain.range_ub = 1.0
            brain.signal_factor_all = 4.0
            brain.signal_factor_mid = 2.5
            brain.signal_factor_left_right = 2.5
            brain.abs_output_bound = 1.0
        else:
            raise NotImplementedError(f"{self._brain_type} brain not implemented yet")

        return brain

    def is_compatible(self, other: NeatBrainGenome, conf: NeatBrainGenomeConfig) -> bool:
        return isinstance(other, NeatBrainGenome) \
               and self._neat_genome.IsCompatibleWith(other._neat_genome, conf.multineat_params)
