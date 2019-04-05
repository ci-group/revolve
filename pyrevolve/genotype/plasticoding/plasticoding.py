# no mother classes have been defined yet! not sure how to separate the the filed in folders...

from enum import Enum
from pyrevolve.genotype import Genotype
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.revolve_module import Orientation
from pyrevolve.revolve_bot.revolve_module import CoreModule
from pyrevolve.revolve_bot.revolve_module import ActiveHingeModule
from pyrevolve.revolve_bot.revolve_module import BrickModule
from pyrevolve.revolve_bot.revolve_module import TouchSensorModule
from pyrevolve.revolve_bot.brain.brain_nn import BrainNN
from pyrevolve.revolve_bot.brain.brain_nn import Node
from pyrevolve.revolve_bot.brain.brain_nn import Connection
from pyrevolve.revolve_bot.brain.brain_nn import Params
import random
import math
import copy


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
        self.quantity_modules = 0
        self.quantity_nodes = 0
        self.index_symbol = 0
        self.index_params = 1
        self.inputs_stack = []
        self.outputs_stack = []
        self.edges = {}

    def clone(self):
        return copy.deepcopy(self)

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

    def develop(self, id_genotype=None):
        self.early_development()
        self.late_development(id_genotype)
        return self.phenotype

    def early_development(self):

        self.intermediate_phenotype = [[self.conf.axiom_w, []]]

        for i in range(0,self.conf.i_iterations):

            position = 0
            for aux_index in range(0, len(self.intermediate_phenotype)):

                symbol = self.intermediate_phenotype[position]
                if [symbol[self.index_symbol], []] in Alphabet.modules():
                    # removes symbol
                    self.intermediate_phenotype.pop(position)
                    # replaces by its production rule
                    for ii in range(0, len(self.grammar[symbol[self.index_symbol]])):
                        self.intermediate_phenotype.insert(position+ii,
                                                           self.grammar[symbol[self.index_symbol]][ii])
                    position = position+ii+1
                else:
                    position = position + 1

    def late_development(self, id_genotype):

        self.phenotype = RevolveBot()
        self.phenotype._brain = BrainNN()
        self.add_imu_nodes()
        block_body_growth = False

        for symbol in self.intermediate_phenotype:

            if symbol[self.index_symbol] == Alphabet.CORE_COMPONENT:
                module = CoreModule()
                self.phenotype._body = module
                module.id = 'module'+str(self.quantity_modules)
                module.orientation = 0
                module.rgb = [1, 1, 0]
                self.mounting_reference = module

            if [symbol[self.index_symbol], []] in Alphabet.morphology_mounting_commands():
                self.morph_mounting_container = symbol[self.index_symbol]

            if [symbol[self.index_symbol], []] in Alphabet.modules() \
                and symbol[self.index_symbol] != Alphabet.CORE_COMPONENT \
                and self.morph_mounting_container is not None:

                if self.mounting_reference.TYPE == 'CoreComponent' \
                   or self.mounting_reference.TYPE == 'FixedBrick':
                    slot = self.get_slot(self.morph_mounting_container).value
                if self.mounting_reference.TYPE == 'ActiveHinge':
                    slot = Orientation.NORTH.value

                if self.quantity_modules < self.conf.max_structural_modules-1:
                    if not block_body_growth:
                        try:
                            self.new_module(slot,
                                            symbol[self.index_symbol],
                                            symbol)
                        except RevolveBot.ItersectionCollisionException as e:
                            self.mounting_reference_stack[-1].children[slot] = None
                            block_body_growth = True

            if [symbol[self.index_symbol], []] in Alphabet.morphology_moving_commands():
                self.move_in_body(symbol)

            if [symbol[self.index_symbol], []] in Alphabet.controller_changing_commands():
                self.decode_brain_changing(symbol)

            if [symbol[self.index_symbol], []] in Alphabet.controller_moving_commands():
                self.decode_brain_moving(symbol)

        # self.phenotype.render2d('experiments/karine_exps/'+str(id_genotype)+'.png')
        # self.phenotype.save_file('experiments/karine_exps/'+str(id_genotype)+'.yaml')

    def move_in_body(self, symbol):

        if symbol[self.index_symbol] == Alphabet.MOVE_BACK \
                and len(self.mounting_reference_stack) > 0:
            self.mounting_reference = self.mounting_reference_stack[-1]
            self.mounting_reference_stack.pop()

        elif symbol[self.index_symbol] == Alphabet.MOVE_FRONT \
                and self.mounting_reference.children[Orientation.NORTH.value] is not None:
            if self.mounting_reference.children[Orientation.NORTH.value].TYPE != 'TouchSensor':
                self.mounting_reference_stack.append(self.mounting_reference)
                self.mounting_reference = \
                    self.mounting_reference.children[Orientation.NORTH.value]

        elif symbol[self.index_symbol] == Alphabet.MOVE_LEFT \
                and self.mounting_reference.TYPE != 'ActiveHinge':
            if self.mounting_reference.children[Orientation.WEST.value] is not None:
                if self.mounting_reference.children[Orientation.WEST.value].TYPE != 'TouchSensor':
                    self.mounting_reference_stack.append(self.mounting_reference)
                    self.mounting_reference = \
                        self.mounting_reference.children[Orientation.WEST.value]

        elif symbol[self.index_symbol] == Alphabet.MOVE_RIGHT \
                and self.mounting_reference.TYPE != 'ActiveHinge':
            if self.mounting_reference.children[Orientation.EAST.value] is not None:
                if self.mounting_reference.children[Orientation.EAST.value].TYPE != 'TouchSensor':
                    self.mounting_reference_stack.append(self.mounting_reference)
                    self.mounting_reference = \
                        self.mounting_reference.children[Orientation.EAST.value]

        elif (symbol[self.index_symbol] == Alphabet.MOVE_RIGHT \
              or symbol[self.index_symbol] == Alphabet.MOVE_LEFT) \
                and self.mounting_reference.TYPE == 'ActiveHinge' \
                and self.mounting_reference.children[Orientation.NORTH.value] is not None:
            self.mounting_reference_stack.append(self.mounting_reference)
            self.mounting_reference = \
                self.mounting_reference.children[Orientation.NORTH.value]

    def decode_brain_changing(self, symbol):

        if len(self.outputs_stack) > 0:

            if symbol[self.index_symbol] == Alphabet.MUTATE_PER:
                self.outputs_stack[0].params.period += float(symbol[self.index_params][0])
                if self.outputs_stack[0].params.period > self.conf.oscillator_param_max:
                    self.outputs_stack[0].params.period = self.conf.oscillator_param_max
                if self.outputs_stack[0].params.period < self.conf.oscillator_param_min:
                    self.outputs_stack[0].params.period = self.conf.oscillator_param_min

            if symbol[self.index_symbol] == Alphabet.MUTATE_AMP:
                self.outputs_stack[0].params.amplitude += float(symbol[self.index_params][0])
                if self.outputs_stack[0].params.amplitude > self.conf.oscillator_param_max:
                    self.outputs_stack[0].params.amplitude = self.conf.oscillator_param_max
                if self.outputs_stack[0].params.amplitude < self.conf.oscillator_param_min:
                    self.outputs_stack[0].params.amplitude = self.conf.oscillator_param_min

            if symbol[self.index_symbol] == Alphabet.MUTATE_OFF:
                self.outputs_stack[0].params.phase_offset += float(symbol[self.index_params][0])
                if self.outputs_stack[0].params.phase_offset > self.conf.oscillator_param_max:
                    self.outputs_stack[0].params.phase_offset = self.conf.oscillator_param_max
                if self.outputs_stack[0].params.phase_offset < self.conf.oscillator_param_min:
                    self.outputs_stack[0].params.phase_offset = self.conf.oscillator_param_min

        if symbol[self.index_symbol] == Alphabet.MUTATE_EDGE:
            if len(self.edges) > 0:
                if (self.inputs_stack[0].id, self.outputs_stack[0].id) in self.edges.keys():
                    self.edges[self.inputs_stack[0].id, self.outputs_stack[0].id].weight \
                        += float(symbol[self.index_params][0])
                    if self.edges[self.inputs_stack[0].id, self.outputs_stack[0].id].weight \
                            > self.conf.weight_param_max:
                        self.edges[self.inputs_stack[0].id, self.outputs_stack[0].id].weight \
                            = self.conf.weight_param_max
                    if self.edges[self.inputs_stack[0].id, self.outputs_stack[0].id].weight \
                            < self.conf.weight_param_min:
                        self.edges[self.inputs_stack[0].id, self.outputs_stack[0].id].weight \
                            = self.conf.weight_param_min

        if len(self.outputs_stack) > 0 and len(self.inputs_stack) > 0:
            if symbol[self.index_symbol] == Alphabet.LOOP:
                if (self.outputs_stack[0].id, self.outputs_stack[0].id) not in self.edges.keys():
                    connection = Connection()
                    connection.src = self.outputs_stack[0].id
                    connection.dst = connection.src
                    connection.weight = float(symbol[self.index_params][0])
                    self.edges[connection.src, connection.src] = connection
                    self.phenotype._brain.connections.append(connection)

            if symbol[self.index_symbol] == Alphabet.ADD_EDGE:
                if (self.inputs_stack[0].id, self.outputs_stack[0].id) not in self.edges.keys():
                    connection = Connection()
                    connection.src = self.inputs_stack[0].id
                    connection.dst = self.outputs_stack[0].id
                    connection.weight = float(symbol[self.index_params][0])
                    self.edges[connection.src, connection.dst] = connection
                    self.phenotype._brain.connections.append(connection)
                    self.inputs_stack[0].output_nodes.append( self.outputs_stack[0])
                    self.outputs_stack[0].input_nodes.append(self.inputs_stack[0])

    def decode_brain_moving(self, symbol):

        if len(self.outputs_stack) > 0 and len(self.inputs_stack) > 0:

            intermediate = int(float(symbol[self.index_params][0]))
            sibling = int(float(symbol[self.index_params][1]))

            if symbol[self.index_symbol] == Alphabet.MOVE_REF_S:

                if len(self.inputs_stack[0].output_nodes) < intermediate:
                    intermediate = len(self.inputs_stack[0].output_nodes) - 1
                else:
                    intermediate = intermediate - 1

                if len(self.inputs_stack[0].output_nodes[intermediate].input_nodes) < sibling:
                    sibling = len(self.inputs_stack[0].output_nodes[intermediate].input_nodes) - 1
                else:
                    sibling = sibling - 1

                self.inputs_stack[0] = self.inputs_stack[0].output_nodes[intermediate].input_nodes[sibling]


            if symbol[self.index_symbol] == Alphabet.MOVE_REF_O:

                if len(self.outputs_stack[0].input_nodes) < intermediate:
                    intermediate = len(self.outputs_stack[0].input_nodes) - 1
                else:
                    intermediate = intermediate - 1

                if len(self.outputs_stack[0].input_nodes[intermediate].output_nodes) < sibling:
                    sibling = len(self.outputs_stack[0].input_nodes[intermediate].output_nodes) - 1
                else:
                    sibling = sibling - 1

                self.outputs_stack[0] = self.outputs_stack[0].input_nodes[intermediate].output_nodes[sibling]

    def get_color(self, new_module_type):

        rgb = []

        if new_module_type == Alphabet.BLOCK:
            rgb = [0, 0, 1]
        if new_module_type == Alphabet.JOINT_HORIZONTAL:
            rgb = [1, 0.08, 0.58]
        if new_module_type == Alphabet.JOINT_VERTICAL:
            rgb = [0.7, 0, 0]
        if new_module_type == Alphabet.SENSOR:
            rgb = [0.7, 0.7, 0.7]
        return rgb

    def get_slot(self, morph_mounting_container):
        slot = None
        if morph_mounting_container == Alphabet.ADD_FRONT:
            slot = Orientation.NORTH
        if morph_mounting_container == Alphabet.ADD_LEFT:
            slot = Orientation.WEST
        if morph_mounting_container == Alphabet.ADD_RIGHT:
            slot = Orientation.EAST
        return slot

    def get_angle(self, new_module_type, parent):
        angle = 0
        if new_module_type == Alphabet.JOINT_VERTICAL:
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

    def new_module(self, slot, new_module_type, symbol):
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

            module.orientation = self.get_angle(new_module_type,
                                                self.mounting_reference)
            module.rgb = self.get_color(new_module_type)
            self.mounting_reference.children[slot] = module
            self.morph_mounting_container = None

            if new_module_type != Alphabet.SENSOR:
                self.quantity_modules += 1
                module.id = 'module' + str(self.quantity_modules)
                self.mounting_reference_stack.append(self.mounting_reference)
                self.mounting_reference = module

                self.phenotype.update_substrate(True)
            else:
                module.id = self.mounting_reference.id+'sensor-'+str(slot)

            if new_module_type == Alphabet.SENSOR \
               or new_module_type == Alphabet.JOINT_HORIZONTAL \
               or new_module_type == Alphabet.JOINT_VERTICAL:
                self.decode_brain_node(symbol, module.id)

    def decode_brain_node(self, symbol, part_id):

        self.quantity_nodes += 1
        node = NodeExtended()
        node.id = 'node'+str(self.quantity_nodes)
        node.weight = float(symbol[self.index_params][0])
        node.part_id = part_id

        if symbol[self.index_symbol] == Alphabet.SENSOR:
            node.layer = 'input'
            node.type = 'Input'

            if len(self.outputs_stack) == 0:
                self.inputs_stack.append(node)
            else:
                if len(self.inputs_stack) > 0:
                    self.inputs_stack = [node]
                else:
                    self.inputs_stack.append(node)

                for output_node in range(0, len(self.outputs_stack)):
                    self.outputs_stack[output_node].input_nodes.append(node)
                    node.output_nodes.append(self.outputs_stack[output_node])

                    connection = Connection()
                    connection.src = node.id
                    connection.dst = self.outputs_stack[output_node].id

                    if output_node == len(self.outputs_stack)-1:
                        connection.weight = node.weight
                    else:
                        connection.weight = float(self.outputs_stack[output_node].weight)
                    self.edges[connection.src, connection.dst] = connection
                    self.phenotype._brain.connections.append(connection)
                self.outputs_stack = [self.outputs_stack[-1]]

            node2 = copy.copy(node)
            node2.id = node.id + '-2'
            self.phenotype._brain.nodes[node.id + '-2'] = node2

        if symbol[self.index_symbol] == Alphabet.JOINT_VERTICAL \
           or symbol[self.index_symbol] == Alphabet.JOINT_HORIZONTAL:
            node.layer = 'output'
            node.type = 'Oscillator'

            params = Params()
            params.period = float(symbol[self.index_params][1])
            params.phase_offset = float(symbol[self.index_params][2])
            params.amplitude = float(symbol[self.index_params][3])
            node.params = params
            self.phenotype._brain.params[node.id] = params

            if len(self.inputs_stack) == 0:
                self.outputs_stack.append(node)
            else:
                if len(self.outputs_stack) > 0:
                    self.outputs_stack = [node]
                else:
                    self.outputs_stack.append(node)

                for input_node in range(0, len(self.inputs_stack)):
                    self.inputs_stack[input_node].output_nodes.append(node)
                    node.input_nodes.append(self.inputs_stack[input_node])

                    connection = Connection()
                    connection.src = self.inputs_stack[input_node].id
                    connection.dst = node.id
                    if input_node == len(self.inputs_stack)-1:
                        connection.weight = node.weight
                    else:
                        connection.weight = float(self.inputs_stack[input_node].weight)
                    self.edges[connection.src, connection.dst] = connection
                    self.phenotype._brain.connections.append(connection)
                self.inputs_stack = [self.inputs_stack[-1]]

        self.phenotype._brain.nodes[node.id] = node

        # print('----')
        # print('>inputs')
        # for i in self.inputs_stack:
        #     print(i.id)
        #     for j in i.output_nodes:
        #         print(' o '+str(j.id))
        # print('>outputs')
        # for i in self.outputs_stack:
        #     print(i.id)
        #     for j in i.input_nodes:
        #         print(' i'+str(j.id))
        # print('>edges')
        # for e in self.edges:
        #     print(e)
        #     print(str(self.edges[e].weight))


    def add_imu_nodes(self):
        for p in range(1, 7):
            id = 'node-code'+str(p)
            node = Node()
            node.layer = 'input'
            node.type = 'Input'
            node.part_id = 'module0'
            node.id = id
            self.phenotype._brain.nodes[id] = node

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


class NodeExtended(Node):
    def __init__(self):
        super().__init__()
        self.weight = None
        self.input_nodes = []
        self.output_nodes = []
        self.params = None


from pyrevolve.genotype.plasticoding import initialization


class PlasticodingConfig:
    def __init__(self,
                 initialization_genome=initialization.random_initialization,
                 e_max_groups=3,
                 oscillator_param_min=1,
                 oscillator_param_max=10,
                 weight_param_min=-1,
                 weight_param_max=1,
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
        self.weight_param_min = weight_param_min
        self.weight_param_max = weight_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.axiom_w = axiom_w
        self.i_iterations = i_iterations
        self.max_structural_modules = max_structural_modules
