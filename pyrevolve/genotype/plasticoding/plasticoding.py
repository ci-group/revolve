# no mother classes have been defined yet! not sure how to separate the the filed in folders...

from enum import Enum
from pyrevolve.genotype import Genotype
import random
import math


class Alphabet(Enum):

    # Modules
    CORE_COMPONENT = 'C'
    JOINT_HORIZONTAL = 'AJ1'
    JOINT_VERTICAL = 'AJ2'
    BLOCK = 'B'
    SENSOR = 'ST'

    # MorphologyMountingCommands
    ADD_RIGHT = 'addr'
    ADD_FRONT = 'addf'
    ADD_LEFT = 'addl'

    # MorphologyMovingCommands
    MOVE_RIGHT = 'mover'
    MOVE_FRONT = 'movef'
    MOVE_LEFT = 'movel'
    MOVE_BACK = 'moveb'

    # ControllerChangingCommands
    ADD_EDGE = 'brainedge'
    MUTATE_EDGE = 'brainperturb'
    LOOP = 'brainloop'
    MUTATE_AMP = 'brainampperturb'
    MUTATE_PER = 'brainperperturb'
    MUTATE_OFF = 'brainoffperturb'

    # ControllerMovingCommands
    MOVE_REF_S = 'brainmoveFTS'
    MOVE_REF_O = 'brainmoveTTS'

    @staticmethod
    def modules():
        return [
            [Alphabet.CORE_COMPONENT,[]],
            [Alphabet.JOINT_HORIZONTAL,[]],
            [Alphabet.JOINT_VERTICAL,[]],
            [Alphabet.BLOCK,[]],
            [Alphabet.SENSOR,[]],
        ]

    @staticmethod
    def morphologyMountingCommands():
        return [
            [Alphabet.ADD_RIGHT,[]],
            [Alphabet.ADD_FRONT,[]],
            [Alphabet.ADD_LEFT,[]]
        ]

    @staticmethod
    def morphologyMovingCommands():
        return [
            [Alphabet.MOVE_RIGHT,[]],
            [Alphabet.MOVE_FRONT,[]],
            [Alphabet.MOVE_LEFT,[]],
            [Alphabet.MOVE_BACK,[]]
        ]

    @staticmethod
    def controllerChangingCommands():
        return [
            [Alphabet.ADD_EDGE,[]],
            [Alphabet.MUTATE_EDGE,[]],
            [Alphabet.LOOP,[]],
            [Alphabet.MUTATE_AMP,[]],
            [Alphabet.MUTATE_PER,[]],
            [Alphabet.MUTATE_OFF,[]]
        ]

    @staticmethod
    def controllerMovingCommands():
        return [
            [Alphabet.MOVE_REF_S,[]],
            [Alphabet.MOVE_REF_O,[]]
        ]


class Plasticoding(Genotype):
    """
    L-system genotypic representation, enhanced with epigenetic capabilities for phenotypic plasticity, through Genetic Programming.
    """

    def __init__(self, conf):
        """
        :param conf:
        :type conf: PlasticodingConfig
        """
        self.conf = conf
        self.grammar = {}
        self.intermediate_phenotype = None
        self.phenotype = None

    def load_genotype(self, genotype_path):
        with open(genotype_path) as f:
            lines = f.readlines()

        for line in lines:
            line_array = line.split(' ')
            repleceable_symbol = Alphabet(line_array[0])
            self.grammar[repleceable_symbol] = []
            rule = line_array[1:len(line_array)-1]
            for s in rule:
                s_array = s.split('_')
                symbol = Alphabet(s_array[0])
                if len(s_array) > 1:
                    params = s_array[1].split('|')
                else:
                    params = []
                self.grammar[repleceable_symbol].append([symbol, params])

    def develop(self, new_genotype, genotype_path=''):

        if new_genotype == 'new':
            self.grammar = self.conf.initialization_genome(self.conf)
        else:
            self.load_genotype(genotype_path)

        print('-------debug genotype------')
        for g in self.grammar:
            print('----')
            print('symbol:', g)
            #print(self.grammar[g])
            for j in range(0, len(self.grammar[g])):
                print(self.grammar[g][j])

        self.early_development();

    def early_development(self):
        print('-------debug early development------')
        self.intermediate_phenotype = [[self.conf.axiom_w, []]]

        for i in range(0,self.conf.i_iterations):
            print('--iteration--'+str(i))

            position = 0
            for aux_index in range(0, len(self.intermediate_phenotype)):
                symbol = self.intermediate_phenotype[position]
                if [symbol[0], []] in Alphabet.modules():
                    # removes symbol
                    self.intermediate_phenotype.pop(position)
                    # replaces by its production rule
                    for ii in range(0, len(self.grammar[symbol[0]])):
                        self.intermediate_phenotype.insert(position+ii,
                                                           self.grammar[symbol[0]][ii])
                    position = position+ii+1
                else:
                    position = position + 1
            #print(self.intermediate_phenotype)
            for j in range(0, len(self.intermediate_phenotype)):
                print(self.intermediate_phenotype[j])

    # adds params for symbols that need it
    # in symbol, [0] has the symbol and [1] the params
    def build_symbol(symbol, conf):
        if symbol[0] == Alphabet.JOINT_HORIZONTAL \
                or symbol[0] == Alphabet.JOINT_VERTICAL:
            symbol[1] = [random.uniform(conf.weight_min, conf.weight_max),
                         random.uniform(conf.oscillator_param_min,
                                        conf.oscillator_param_max),
                         random.uniform(conf.oscillator_param_min,
                                        conf.oscillator_param_max),
                         random.uniform(conf.oscillator_param_min,
                                        conf.oscillator_param_max)]

        if symbol[0] == Alphabet.SENSOR  \
                or symbol[0] == Alphabet.ADD_EDGE \
                or symbol[0] == Alphabet.LOOP:
            symbol[1] = [random.uniform(conf.weight_min, conf.weight_max)]

        if symbol[0] == Alphabet.MUTATE_EDGE \
            or symbol[0] == Alphabet.MUTATE_AMP \
            or symbol[0] == Alphabet.MUTATE_PER \
            or symbol[0] == Alphabet.MUTATE_OFF:
                symbol[1] = [random.normalvariate(0, 1)]

        if symbol[0] == Alphabet.MOVE_REF_S \
                or symbol[0] == Alphabet.MOVE_REF_O:
            intermediate_temp = random.normalvariate(0, 1)
            final_temp = random.normalvariate(0, 1)
            symbol[1] = [math.ceil(math.sqrt(math.pow(intermediate_temp, 2))),
                         math.ceil(math.sqrt(math.pow(final_temp, 2)))]

        return symbol


from pyrevolve.genotype.plasticoding import initialization


class PlasticodingConfig:
    def __init__(self,
                 initialization_genome=initialization.random_initialization,
                 e_max_groups=3,
                 oscillator_param_min=1,
                 oscillator_param_max=10,
                 weight_min=-1,
                 weight_max=1,
                 axiom_w=Alphabet.CORE_COMPONENT,
                 i_iterations=3
                 ):
        self.initialization_genome = initialization_genome
        self.e_max_groups = e_max_groups
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.axiom_w = axiom_w
        self.i_iterations = i_iterations
