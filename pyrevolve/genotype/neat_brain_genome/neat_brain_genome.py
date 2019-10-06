from pyrevolve.genotype import Genotype
from pyrevolve.revolve_bot.brain.cpg import BrainCPG
import enum
import multineat


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

        # HyperNEAT-CPG section
        self.hyperneat_with_distance_input = False

        # generate multineat params object
        self.multineat_params = self._generate_multineat_params(brain_type)

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
    def __init__(self, conf: NeatBrainGenomeConfig = None, robot_id: int = None):
        self._net = multineat.NeuralNetwork()

        if conf is None:
            self._brain_type = None
            self._neat_genome = None
            return

        self.id = int(robot_id)
        self._brain_type = conf.brain_type
        is_cppn = conf.is_brain_cppn()

        if is_cppn:

            # if HyperNEAT
            if conf.brain_type is BrainType.CPG:
                # calculate number of inputs
                n_coordinates = 3
                conf.n_inputs = n_coordinates * 2
                if conf.hyperneat_with_distance_input:
                    conf.n_inputs += 1
                # Always count the bias
                conf.n_inputs += 1

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

    # override
    def clone(self):
        clone = NeatBrainGenome()
        clone._brain_type = self._brain_type  # the conf must not be deep copied
        clone._neat_genome = multineat.Genome(self._neat_genome)

    @property
    def id(self):
        return f"{self._neat_genome.GedID()}"

    @id.setter
    def id(self, value: int):
        self._neat_genome.SetID(value)

    def develop(self):
        if self.brain_type is BrainType.CPG:
            # basically, HyperNEAT
            brain = BrainCPG()
            self._neat_genome.BuildPhenotype(self._net)
            for coord in brain.weights_coordinates():
                # TODO check this
                _input = coord
                self._net.Flush()
                self._net.Input(_input)
                self._net.Activate()
                output = self._net.Output()[0]
                brain.set_weight(coord, output)
            raise NotImplementedError("CPG brain implementation not finished yet")
        else:
            raise NotImplementedError(f"{self.brain_type} brain not implemented yet")

        return brain
