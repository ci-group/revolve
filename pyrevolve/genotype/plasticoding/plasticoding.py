# no mother classes have been defined yet! not sure how to separate the the filed in folders...

from enum import Enum
from pyrevolve.genotype import Genotype
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.revolve_module import Orientation
from pyrevolve.revolve_bot.revolve_module import CoreModule
from pyrevolve.revolve_bot.revolve_module import ActiveHingeModule
from pyrevolve.revolve_bot.revolve_module import BrickModule
from pyrevolve.revolve_bot.revolve_module import TouchSensorModule
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
            [Alphabet.CORE_COMPONENT, []],
            [Alphabet.JOINT_HORIZONTAL, []],
            [Alphabet.JOINT_VERTICAL, []],
            [Alphabet.BLOCK, []],
            [Alphabet.SENSOR, []],
        ]

    @staticmethod
    def morphology_mounting_commands():
        return [
            [Alphabet.ADD_RIGHT, []],
            [Alphabet.ADD_FRONT, []],
            [Alphabet.ADD_LEFT, []]
        ]

    @staticmethod
    def morphology_moving_commands():
        return [
            [Alphabet.MOVE_RIGHT, []],
            [Alphabet.MOVE_FRONT, []],
            [Alphabet.MOVE_LEFT, []],
            [Alphabet.MOVE_BACK, []]
        ]

    @staticmethod
    def controller_changing_commands():
        return [
            [Alphabet.ADD_EDGE, []],
            [Alphabet.MUTATE_EDGE, []],
            [Alphabet.LOOP, []],
            [Alphabet.MUTATE_AMP, []],
            [Alphabet.MUTATE_PER, []],
            [Alphabet.MUTATE_OFF, []]
        ]

    @staticmethod
    def controller_moving_commands():
        return [
            [Alphabet.MOVE_REF_S, []],
            [Alphabet.MOVE_REF_O, []]
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
        self.morph_mounting_container = None
        self.mounting_reference = None
        self.mounting_reference_stack = []
        self.quantity_components = 0

    def load_genotype(self, genotype_path):
        with open(genotype_path) as f:
            lines = f.readlines()

        for line in lines:
            line_array = line.split(' ')
            repleceable_symbol = Alphabet(line_array[0])
            self.grammar[repleceable_symbol] = []
            rule = line_array[1:len(line_array)-1]
            for symbol_array in rule:
                symbol_array = symbol_array.split('_')
                symbol = Alphabet(symbol_array[0])
                if len(symbol_array) > 1:
                    params = symbol_array[1].split('|')
                else:
                    params = []
                self.grammar[repleceable_symbol].append([symbol, params])

    def develop(self, new_genotype, genotype_path='', id_genotype=None):

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

        self.early_development()
        self.late_development(id_genotype)

    def early_development(self):
        index_symbol = 0
        print('-------debug early development------')
        self.intermediate_phenotype = [[self.conf.axiom_w, []]]

        for i in range(0,self.conf.i_iterations):
            print('--iteration--'+str(i))

            position = 0
            for aux_index in range(0, len(self.intermediate_phenotype)):

                symbol = self.intermediate_phenotype[position]
                if [symbol[index_symbol], []] in Alphabet.modules():
                    # removes symbol
                    self.intermediate_phenotype.pop(position)
                    # replaces by its production rule
                    for ii in range(0, len(self.grammar[symbol[index_symbol]])):
                        self.intermediate_phenotype.insert(position+ii,
                                                           self.grammar[symbol[index_symbol]][ii])
                    position = position+ii+1
                else:
                    position = position + 1
            #print(self.intermediate_phenotype)
            for j in range(0, len(self.intermediate_phenotype)):
                print(self.intermediate_phenotype[j])

    def late_development(self, id_genotype):

        index_symbol = 0
        index_params = 1
        self.phenotype = RevolveBot()

        print('-------debug late development------')
        for symbol in self.intermediate_phenotype:
            print('---symbol')
            print(symbol)
            # start mounting by the head
            if symbol[index_symbol] == Alphabet.CORE_COMPONENT:
                module = CoreModule()
                self.phenotype._body = module
                module.id = 'module'+str(self.quantity_components)
                print('id')
                print(self.quantity_components)
                module.orientation = 0
                self.mounting_reference = module

            if [symbol[index_symbol], []] in Alphabet.morphology_mounting_commands():
                self.morph_mounting_container = symbol[index_symbol]

            if [symbol[index_symbol], []] in Alphabet.morphology_moving_commands():

                if symbol[index_symbol] == Alphabet.MOVE_BACK \
                   and len(self.mounting_reference_stack) > 0:
                    self.mounting_reference = self.mounting_reference_stack[-1]
                    self.mounting_reference_stack.pop()

                elif symbol[index_symbol] == Alphabet.MOVE_FRONT \
                   and self.mounting_reference.children[Orientation.NORTH.value] is not None:
                        if self.mounting_reference.children[Orientation.NORTH.value].TYPE != 'TouchSensor':
                            self.mounting_reference_stack.append(self.mounting_reference)
                            self.mounting_reference = \
                                self.mounting_reference.children[Orientation.NORTH.value]

                elif symbol[index_symbol] == Alphabet.MOVE_LEFT \
                   and self.mounting_reference.TYPE != 'ActiveHinge':
                        if self.mounting_reference.children[Orientation.WEST.value] is not None:
                            if self.mounting_reference.children[Orientation.WEST.value].TYPE != 'TouchSensor':
                                self.mounting_reference_stack.append(self.mounting_reference)
                                self.mounting_reference = \
                                    self.mounting_reference.children[Orientation.WEST.value]

                elif symbol[index_symbol] == Alphabet.MOVE_RIGHT \
                   and self.mounting_reference.TYPE != 'ActiveHinge':
                        if self.mounting_reference.children[Orientation.EAST.value] is not None:
                            if self.mounting_reference.children[Orientation.EAST.value].TYPE != 'TouchSensor':
                                self.mounting_reference_stack.append(self.mounting_reference)
                                self.mounting_reference = \
                                    self.mounting_reference.children[Orientation.EAST.value]

                elif (symbol[index_symbol] == Alphabet.MOVE_RIGHT \
                   or symbol[index_symbol] == Alphabet.MOVE_LEFT) \
                   and self.mounting_reference.TYPE == 'ActiveHinge' \
                   and self.mounting_reference.children[Orientation.NORTH.value] is not None:
                        self.mounting_reference_stack.append(self.mounting_reference)
                        self.mounting_reference = \
                            self.mounting_reference.children[Orientation.NORTH.value]


            # mount other body parts
            if [symbol[index_symbol], []] in Alphabet.modules() \
                and symbol[index_symbol] != Alphabet.CORE_COMPONENT \
                    and self.morph_mounting_container is not None:

                if self.mounting_reference.TYPE == 'CoreComponent' \
                   or self.mounting_reference.TYPE == 'FixedBrick':
                    slot = self.get_slot(self.morph_mounting_container).value
                if self.mounting_reference.TYPE == 'ActiveHinge':
                    slot = Orientation.NORTH.value
                print('container')
                print(self.morph_mounting_container)
                if self.quantity_components < self.conf.max_structural_modules:
                    self.new_module(slot,
                                    symbol[index_symbol])
            print('ref '+str(self.mounting_reference.id))
            print(self.mounting_reference.TYPE)
            print(self.mounting_reference.children)


            self.phenotype.render2d('experiments/karine_exps/'+str(id_genotype)+'.png');
        #self.phenotype.save_file('experiments/karine_exps/'+str(id_genotype)+'.yaml')

    def get_slot(self, morph_mounting_container):

        slot = None
        if morph_mounting_container == Alphabet.ADD_FRONT:
            slot = Orientation.NORTH
        if morph_mounting_container == Alphabet.ADD_LEFT:
            slot = Orientation.WEST
        if morph_mounting_container == Alphabet.ADD_RIGHT:
            slot = Orientation.EAST
        return slot

    def get_angle(self, module, parent):
        angle = 0
        if module == Alphabet.JOINT_VERTICAL:
            if parent.TYPE == 'ActiveHinge' \
                    and parent.orientation == 90:
                angle = 0
            else:
                angle = 90
        else:
            if parent.TYPE == 'ActiveHinge' \
                    and parent.orientation == 90:
                angle = 270
        return angle

    def new_module(self, slot, new_module_type):

        mount = 'no'
        if self.mounting_reference.children[slot] is None \
           and not (new_module_type == Alphabet.SENSOR
                    and self.mounting_reference.TYPE == 'ActiveHinge'):
            mount = 'yes'

        if self.mounting_reference.TYPE == 'CoreComponent' \
                and self.mounting_reference.children[1] is not None \
                and self.mounting_reference.children[2] is not None \
                and self.mounting_reference.children[3] is not None \
                and self.mounting_reference.children[0] is None:
            slot = 0
            mount = 'yes'

        if mount == 'yes':
            if new_module_type == Alphabet.BLOCK:
                module = BrickModule()
            if new_module_type == Alphabet.JOINT_VERTICAL \
                    or new_module_type == Alphabet.JOINT_HORIZONTAL:
                module = ActiveHingeModule()
            if new_module_type == Alphabet.SENSOR:
                module = TouchSensorModule()

            self.quantity_components += 1
            module.id = 'module'+str(self.quantity_components)
            module.orientation = self.get_angle(new_module_type,
                                                self.mounting_reference)
            self.mounting_reference.children[slot] = module
            self.morph_mounting_container = None

            if new_module_type != Alphabet.SENSOR:
                self.mounting_reference_stack.append(self.mounting_reference)
                self.mounting_reference = module


    # adds params for symbols that need it
    @staticmethod
    def build_symbol(symbol, conf):

        index_symbol = 0
        index_params = 1

        if symbol[index_symbol] == Alphabet.JOINT_HORIZONTAL \
                or symbol[index_symbol] == Alphabet.JOINT_VERTICAL:
            symbol[index_params] = [random.uniform(conf.weight_min, conf.weight_max),
                                    random.uniform(conf.oscillator_param_min,
                                                   conf.oscillator_param_max),
                                    random.uniform(conf.oscillator_param_min,
                                                   conf.oscillator_param_max),
                                    random.uniform(conf.oscillator_param_min,
                                                   conf.oscillator_param_max)]

        if symbol[index_symbol] == Alphabet.SENSOR  \
                or symbol[index_symbol] == Alphabet.ADD_EDGE \
                or symbol[index_symbol] == Alphabet.LOOP:
            symbol[index_params] = [random.uniform(conf.weight_min, conf.weight_max)]

        if symbol[index_symbol] == Alphabet.MUTATE_EDGE \
            or symbol[index_symbol] == Alphabet.MUTATE_AMP \
            or symbol[index_symbol] == Alphabet.MUTATE_PER \
            or symbol[index_symbol] == Alphabet.MUTATE_OFF:
                symbol[index_params] = [random.normalvariate(0, 1)]

        if symbol[index_symbol] == Alphabet.MOVE_REF_S \
                or symbol[index_symbol] == Alphabet.MOVE_REF_O:
            intermediate_temp = random.normalvariate(0, 1)
            final_temp = random.normalvariate(0, 1)
            symbol[index_params] = [math.ceil(math.sqrt(math.pow(intermediate_temp, 2))),
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
                 i_iterations=3,
                 max_structural_modules=100
                 ):
        self.initialization_genome = initialization_genome
        self.e_max_groups = e_max_groups
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.axiom_w = axiom_w
        self.i_iterations = i_iterations
        self.max_structural_modules = max_structural_modules
