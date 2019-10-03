from pyrevolve.genotype.plasticoding.alphabet import Alphabet, INDEX_SYMBOL, INDEX_PARAMS
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.brain import BrainNN
from pyrevolve.revolve_bot.brain.brain_nn import Connection, Node, Params
from pyrevolve.revolve_bot.revolve_module import Orientation, CoreModule, BrickModule, ActiveHingeModule, \
    TouchSensorModule


# Early Development
class GrammarExpander:
    def __init__(self, genotype):
        """
        Plasticoding late development decoder
        :param genotype: Plasticoding genotype object
        :type genotype: Plasticoding
        """
        self._genotype = genotype
        self._grammar = genotype.grammar
        self._conf = genotype.conf

    def expand_grammar(self, n_iterations: int, axiom=Alphabet.CORE_COMPONENT):
        """
        Expands the grammar in a command sentence wrapped inside a PlasticodingDecoder
        :param n_iterations: number of iterations of the grammar expansion
        :param axiom: starting axiom of the grammar
        :type axiom: Alphabet
        :return: sentence wrapped inside a PlasticodingDecoder ready to be decoded
        :rtype PlasticodingDecoder
        """
        developed_sentence = [(axiom, [])]

        for i in range(0, n_iterations):

            position = 0
            for aux_index in range(0, len(developed_sentence)):

                symbol = developed_sentence[position][INDEX_SYMBOL]
                # TODO check if is present in production rules instead, don't assume production rules and modules are
                #  the same
                if symbol in Alphabet.modules(self._conf.allow_vertical_brick):
                    # removes symbol
                    developed_sentence.pop(position)
                    # replaces by its production rule
                    ii = 0
                    for ii in range(0, len(self._grammar[symbol])):
                        developed_sentence.insert(position + ii, self._grammar[symbol][ii])
                    position = position + ii + 1
                else:
                    position = position + 1
        # logger.info('Robot ' + str(self.id) + ' was early-developed.')
        return PlasticodingDecoder(self._genotype.id, self._conf, developed_sentence)


# Late Development
class PlasticodingDecoder:
    def __init__(self, id_, conf, command_sentence):
        """
        Plasticoding late development decoder
        :param id_: the id of the genome
        :type id_: int|str
        :param conf: Plasticoding configuration object
        :type conf: PlasticodingConfig
        :param command_sentence: result of the early developmental stage
        """
        self._id = id_
        self._conf = conf
        self._command_sentence = command_sentence
        self.body = RevolveBot()
        self.brain = BrainNN()

        self.mounting_reference = None
        self.mounting_reference_stack = []
        self.morph_mounting_container = None
        self.quantity_modules = 1
        self.quantity_nodes = 0
        self.inputs_stack = []
        self.outputs_stack = []
        self.edges = {}
        self.substrate_coordinates_all = {(0, 0): '1'}

    class Cursor:
        def __init__(self, current_module):
            self._current_module = current_module

    class CursorStack:
        def __init__(self):
            self._stack = []

        def pop(self):
            self._stack.pop()

        def push(self, cursor):
            self._stack.append(cursor)

    def decode_sentence(self):
        self.body._id = self._id if type(self._id) == str and self._id.startswith('robot') \
            else f'robot_{self._id}'

        for symbol in self._command_sentence:

            if symbol[INDEX_SYMBOL] == Alphabet.CORE_COMPONENT:
                assert(self.mounting_reference is None)
                module = CoreModule()
                self.body._body = module
                module.id = str(self.quantity_modules)
                module.info = {'orientation': Orientation.NORTH,
                               'new_module_type': Alphabet.CORE_COMPONENT}
                module.orientation = 0
                module.rgb = [1, 1, 0]
                self.mounting_reference = module

            elif symbol[INDEX_SYMBOL] in Alphabet.morphology_mounting_commands():
                assert(self.mounting_reference is not None)
                self.morph_mounting_container = symbol[INDEX_SYMBOL]

            elif symbol[INDEX_SYMBOL] in Alphabet.modules(self._conf.allow_vertical_brick) \
                    and symbol[INDEX_SYMBOL] is not Alphabet.CORE_COMPONENT:
                if self.morph_mounting_container is not None:
                    assert(self.mounting_reference is not None)

                    if type(self.mounting_reference) == CoreModule \
                            or type(self.mounting_reference) == BrickModule:
                        slot = self.get_slot(self.morph_mounting_container).value
                    elif type(self.mounting_reference) == ActiveHingeModule:
                        slot = Orientation.NORTH.value
                    else:
                        raise RuntimeError(f'Mounting reference {type(self.mounting_reference)} does not support a mount')

                    if self.quantity_modules < self._conf.max_structural_modules:
                        self.new_module(slot,
                                        symbol[INDEX_SYMBOL],
                                        symbol)

            elif symbol[INDEX_SYMBOL] in Alphabet.morphology_moving_commands(self._conf.use_movement_commands,
                                                                             self._conf.use_rotation_commands,
                                                                             self._conf.use_movement_stack):
                assert(self.mounting_reference is not None)
                self.move_in_body(symbol)

            elif symbol[INDEX_SYMBOL] in Alphabet.controller_changing_commands():
                assert(self.mounting_reference is not None)
                self.decode_brain_changing(symbol)

            elif symbol[INDEX_SYMBOL] in Alphabet.controller_moving_commands():
                assert(self.mounting_reference is not None)
                self.decode_brain_moving(symbol)

            else:
                raise RuntimeError(f'Unrecognized symbol: {symbol[INDEX_SYMBOL]}')

        self.add_imu_nodes()

        self.body._brain = self.brain
        return self.body

    @staticmethod
    def get_slot(morph_mounting_container):
        slot = None
        if morph_mounting_container == Alphabet.ADD_FRONT:
            slot = Orientation.NORTH
        elif morph_mounting_container == Alphabet.ADD_LEFT:
            slot = Orientation.WEST
        elif morph_mounting_container == Alphabet.ADD_RIGHT:
            slot = Orientation.EAST
        return slot

    def get_angle(self, new_module_type, parent):
        if self._conf.use_rotation_commands:
            pending_rotation = parent.info.get('pending_rotation') or 0
            return parent.orientation + pending_rotation
        else:
            angle = 0
            vertical_new_module = new_module_type.is_vertical_module()
            vertical_parent = parent.info['new_module_type'].is_vertical_module()
            if vertical_new_module and not vertical_parent:
                angle = 90
            elif vertical_parent and not vertical_new_module:
                angle = 270
            return angle

    @staticmethod
    def get_color(new_module_type):
        if new_module_type == Alphabet.BLOCK:
            rgb = [0.0, 0.0, 1.0]
        elif new_module_type == Alphabet.BLOCK_VERTICAL:
            rgb = [0.5, 0.5, 1.0]
        elif new_module_type == Alphabet.JOINT_HORIZONTAL:
            rgb = [1.0, 0.08, 0.58]
        elif new_module_type == Alphabet.JOINT_VERTICAL:
            rgb = [0.7, 0.0, 0.0]
        elif new_module_type == Alphabet.SENSOR:
            rgb = [0.7, 0.7, 0.7]
        else:
            rgb = [1.0, 1.0, 1.0]
        return rgb

    def move_in_body(self, symbol):
        if symbol[INDEX_SYMBOL] == Alphabet.MOVE_BACK \
                and len(self.mounting_reference_stack) > 0:
            self.mounting_reference = self.mounting_reference_stack[-1]
            self.mounting_reference_stack.pop()

        elif symbol[INDEX_SYMBOL] == Alphabet.MOVE_FRONT \
                and self.mounting_reference.children[Orientation.NORTH.value] is not None:
            if type(self.mounting_reference.children[Orientation.NORTH.value]) is not TouchSensorModule:
                self.mounting_reference_stack.append(self.mounting_reference)
                self.mounting_reference = \
                    self.mounting_reference.children[Orientation.NORTH.value]

        elif symbol[INDEX_SYMBOL] == Alphabet.MOVE_LEFT \
                and type(self.mounting_reference) is not ActiveHingeModule:
            if self.mounting_reference.children[Orientation.WEST.value] is not None:
                if type(self.mounting_reference.children[Orientation.WEST.value]) is not TouchSensorModule:
                    self.mounting_reference_stack.append(self.mounting_reference)
                    self.mounting_reference = \
                        self.mounting_reference.children[Orientation.WEST.value]

        elif symbol[INDEX_SYMBOL] == Alphabet.MOVE_RIGHT \
                and type(self.mounting_reference) is not ActiveHingeModule:
            if self.mounting_reference.children[Orientation.EAST.value] is not None:
                if type(self.mounting_reference.children[Orientation.EAST.value]) is not TouchSensorModule:
                    self.mounting_reference_stack.append(self.mounting_reference)
                    self.mounting_reference = \
                        self.mounting_reference.children[Orientation.EAST.value]

        elif (symbol[INDEX_SYMBOL] == Alphabet.MOVE_RIGHT \
              or symbol[INDEX_SYMBOL] == Alphabet.MOVE_LEFT) \
                and type(self.mounting_reference) is ActiveHingeModule \
                and self.mounting_reference.children[Orientation.NORTH.value] is not None:
            self.mounting_reference_stack.append(self.mounting_reference)
            self.mounting_reference = \
                self.mounting_reference.children[Orientation.NORTH.value]

        elif symbol[INDEX_SYMBOL] is Alphabet.ROTATE_90 \
                or symbol[INDEX_SYMBOL] is Alphabet.ROTATE_N90:
            rotation = self.mounting_reference.info.get('pending_rotation') or 0
            rotation += 90 if symbol[INDEX_SYMBOL] is Alphabet.ROTATE_90 else -90
            self.mounting_reference.info['pending_rotation'] = rotation

    def new_module(self, slot, new_module_type, symbol):
        mount = False
        if self.mounting_reference.children[slot] is None \
                and not (new_module_type == Alphabet.SENSOR
                         and type(self.mounting_reference) is ActiveHingeModule):
            mount = True

        if type(self.mounting_reference) is CoreModule \
                and self.mounting_reference.children[1] is not None \
                and self.mounting_reference.children[2] is not None \
                and self.mounting_reference.children[3] is not None \
                and self.mounting_reference.children[0] is None:
            slot = 0
            mount = True

        if mount:
            if new_module_type == Alphabet.BLOCK \
                    or new_module_type == Alphabet.BLOCK_VERTICAL:
                module = BrickModule()
            elif new_module_type == Alphabet.JOINT_VERTICAL \
                    or new_module_type == Alphabet.JOINT_HORIZONTAL:
                module = ActiveHingeModule()
            elif new_module_type == Alphabet.SENSOR:
                module = TouchSensorModule()
            else:
                raise NotImplementedError(f'{new_module_type}')

            module.info = {'new_module_type': new_module_type}
            module.orientation = self.get_angle(new_module_type,
                                                self.mounting_reference)
            module.rgb = self.get_color(new_module_type)

            if new_module_type != Alphabet.SENSOR:
                self.quantity_modules += 1
                module.id = str(self.quantity_modules)
                intersection = self.check_intersection(self.mounting_reference, slot, module)

                if not intersection:
                    self.mounting_reference.children[slot] = module
                    self.morph_mounting_container = None
                    self.mounting_reference_stack.append(self.mounting_reference)
                    self.mounting_reference = module
                    if new_module_type == Alphabet.JOINT_HORIZONTAL \
                            or new_module_type == Alphabet.JOINT_VERTICAL:
                        self.decode_brain_node(symbol, module.id)
                else:
                    self.quantity_modules -= 1
            else:
                self.mounting_reference.children[slot] = module
                self.morph_mounting_container = None
                module.id = self.mounting_reference.id + 's' + str(slot)
                self.decode_brain_node(symbol, module.id)

    def check_intersection(self, parent, slot, module):
        """
        Update coordinates of module
        :return:
        """
        dic = {Orientation.NORTH.value: 0,
               Orientation.WEST.value: 1,
               Orientation.SOUTH.value: 2,
               Orientation.EAST.value: 3}

        inverse_dic = {0: Orientation.NORTH.value,
                       1: Orientation.WEST.value,
                       2: Orientation.SOUTH.value,
                       3: Orientation.EAST.value}

        direction = dic[parent.info['orientation'].value] + dic[slot]
        if direction >= len(dic):
            direction = direction - len(dic)

        new_direction = Orientation(inverse_dic[direction])
        if new_direction == Orientation.WEST:
            coordinates = [parent.substrate_coordinates[0],
                           parent.substrate_coordinates[1] - 1]
        elif new_direction == Orientation.EAST:
            coordinates = [parent.substrate_coordinates[0],
                           parent.substrate_coordinates[1] + 1]
        elif new_direction == Orientation.NORTH:
            coordinates = [parent.substrate_coordinates[0] + 1,
                           parent.substrate_coordinates[1]]
        elif new_direction == Orientation.SOUTH:
            coordinates = [parent.substrate_coordinates[0] - 1,
                           parent.substrate_coordinates[1]]
        else:
            raise NotImplemented()

        module.substrate_coordinates = coordinates
        module.info['orientation'] = new_direction
        if (coordinates[0], coordinates[1]) in self.substrate_coordinates_all:
            return True
        else:
            self.substrate_coordinates_all[coordinates[0],
                                           coordinates[1]] = module.id
            return False

    def decode_brain_node(self, symbol, part_id):
        from pyrevolve.genotype.plasticoding.plasticoding import NodeExtended

        self.quantity_nodes += 1
        node = NodeExtended()
        node.id = f'node{self.quantity_nodes}'
        node.weight = float(symbol[INDEX_PARAMS][0])
        node.part_id = part_id

        if symbol[INDEX_SYMBOL] == Alphabet.SENSOR:

            node.layer = 'input'
            node.type = 'Input'

            # stacks sensor if there are no oscillators yet
            if len(self.outputs_stack) == 0:
                self.inputs_stack.append(node)
            else:
                # if it is the first senor ever
                if len(self.inputs_stack) > 0:
                    self.inputs_stack = [node]
                else:
                    self.inputs_stack.append(node)

                # connects sensor to all oscillators in the stack
                for output_node in range(0, len(self.outputs_stack)):
                    self.outputs_stack[output_node].input_nodes.append(node)
                    node.output_nodes.append(self.outputs_stack[output_node])

                    connection = Connection()
                    connection.src = node.id
                    connection.dst = self.outputs_stack[output_node].id

                    if output_node == len(self.outputs_stack) - 1:
                        connection.weight = node.weight
                    else:
                        connection.weight = float(self.outputs_stack[output_node].weight)
                    self.edges[connection.src, connection.dst] = connection
                    self.brain.connections.append(connection)
                self.outputs_stack = [self.outputs_stack[-1]]

        if symbol[INDEX_SYMBOL] == Alphabet.JOINT_VERTICAL \
                or symbol[INDEX_SYMBOL] == Alphabet.JOINT_HORIZONTAL:

            node.layer = 'output'
            node.type = 'Oscillator'

            params = Params()
            params.period = float(symbol[INDEX_PARAMS][1])
            params.phase_offset = float(symbol[INDEX_PARAMS][2])
            params.amplitude = float(symbol[INDEX_PARAMS][3])
            node.params = params
            self.brain.params[node.id] = params

            # stacks oscillator if there are no sensors yet
            if len(self.inputs_stack) == 0:
                self.outputs_stack.append(node)
            else:
                # if it is the first oscillator ever
                if len(self.outputs_stack) > 0:
                    self.outputs_stack = [node]
                else:
                    self.outputs_stack.append(node)

                # connects oscillator to all sensors in the stack
                for input_node in range(0, len(self.inputs_stack)):
                    self.inputs_stack[input_node].output_nodes.append(node)
                    node.input_nodes.append(self.inputs_stack[input_node])

                    connection = Connection()
                    connection.src = self.inputs_stack[input_node].id
                    connection.dst = node.id
                    if input_node == len(self.inputs_stack) - 1:
                        connection.weight = node.weight
                    else:
                        connection.weight = float(self.inputs_stack[input_node].weight)
                    self.edges[connection.src, connection.dst] = connection
                    self.brain.connections.append(connection)
                self.inputs_stack = [self.inputs_stack[-1]]

        self.brain.nodes[node.id] = node

    def add_imu_nodes(self):
        for p in range(1, 7):
            _id = 'node-core' + str(p)
            node = Node()
            node.layer = 'input'
            node.type = 'Input'
            node.part_id = self.body.id
            node.id = _id
            self.brain.nodes[_id] = node

    def decode_brain_moving(self, symbol):

        # if there is at least both one sensor and one oscillator
        if len(self.outputs_stack) > 0 and len(self.inputs_stack) > 0:

            intermediate = int(float(symbol[INDEX_PARAMS][0]))
            sibling = int(float(symbol[INDEX_PARAMS][1]))

            if symbol[INDEX_SYMBOL] == Alphabet.MOVE_REF_S:

                if len(self.inputs_stack[-1].output_nodes) < intermediate:
                    intermediate = len(self.inputs_stack[-1].output_nodes) - 1
                else:
                    intermediate = intermediate - 1

                if len(self.inputs_stack[-1].output_nodes[intermediate].input_nodes) < sibling:
                    sibling = len(self.inputs_stack[-1].output_nodes[intermediate].input_nodes) - 1
                else:
                    sibling = sibling - 1

                self.inputs_stack[-1] = self.inputs_stack[-1].output_nodes[intermediate].input_nodes[sibling]

            if symbol[INDEX_SYMBOL] == Alphabet.MOVE_REF_O:

                if len(self.outputs_stack[-1].input_nodes) < intermediate:
                    intermediate = len(self.outputs_stack[-1].input_nodes) - 1
                else:
                    intermediate = intermediate - 1

                if len(self.outputs_stack[-1].input_nodes[intermediate].output_nodes) < sibling:
                    sibling = len(self.outputs_stack[-1].input_nodes[intermediate].output_nodes) - 1
                else:
                    sibling = sibling - 1

                self.outputs_stack[-1] = self.outputs_stack[-1].input_nodes[intermediate].output_nodes[sibling]

    def decode_brain_changing(self, symbol):
        conf = self._conf

        # if there is at least both one oscillator
        if len(self.outputs_stack) > 0:

            if symbol[INDEX_SYMBOL] == Alphabet.MUTATE_PER:
                self.outputs_stack[-1].params.period += float(symbol[INDEX_PARAMS][0])
                if self.outputs_stack[-1].params.period > conf.oscillator_param_max:
                    self.outputs_stack[-1].params.period = conf.oscillator_param_max
                if self.outputs_stack[-1].params.period < conf.oscillator_param_min:
                    self.outputs_stack[-1].params.period = conf.oscillator_param_min

            if symbol[INDEX_SYMBOL] == Alphabet.MUTATE_AMP:
                self.outputs_stack[-1].params.amplitude += float(symbol[INDEX_PARAMS][0])
                if self.outputs_stack[-1].params.amplitude > conf.oscillator_param_max:
                    self.outputs_stack[-1].params.amplitude = conf.oscillator_param_max
                if self.outputs_stack[-1].params.amplitude < conf.oscillator_param_min:
                    self.outputs_stack[-1].params.amplitude = conf.oscillator_param_min

            if symbol[INDEX_SYMBOL] == Alphabet.MUTATE_OFF:
                self.outputs_stack[-1].params.phase_offset += float(symbol[INDEX_PARAMS][0])
                if self.outputs_stack[-1].params.phase_offset > conf.oscillator_param_max:
                    self.outputs_stack[-1].params.phase_offset = conf.oscillator_param_max
                if self.outputs_stack[-1].params.phase_offset < conf.oscillator_param_min:
                    self.outputs_stack[-1].params.phase_offset = conf.oscillator_param_min

        if symbol[INDEX_SYMBOL] == Alphabet.MUTATE_EDGE:
            if len(self.edges) > 0:
                if (self.inputs_stack[-1].id, self.outputs_stack[-1].id) in self.edges.keys():
                    self.edges[self.inputs_stack[-1].id, self.outputs_stack[-1].id].weight \
                        += float(symbol[INDEX_PARAMS][0])
                    if self.edges[self.inputs_stack[-1].id, self.outputs_stack[-1].id].weight \
                            > conf.weight_param_max:
                        self.edges[self.inputs_stack[-1].id, self.outputs_stack[-1].id].weight \
                            = conf.weight_param_max
                    if self.edges[self.inputs_stack[-1].id, self.outputs_stack[-1].id].weight \
                            < conf.weight_param_min:
                        self.edges[self.inputs_stack[-1].id, self.outputs_stack[-1].id].weight \
                            = conf.weight_param_min

        # if there is at least both one sensor and one oscillator
        if len(self.outputs_stack) > 0 and len(self.inputs_stack) > 0:
            if symbol[INDEX_SYMBOL] == Alphabet.LOOP:

                if (self.outputs_stack[-1].id, self.outputs_stack[-1].id) not in self.edges.keys():
                    connection = Connection()
                    connection.src = self.outputs_stack[-1].id
                    connection.dst = connection.src
                    connection.weight = float(symbol[INDEX_PARAMS][0])
                    self.edges[connection.src, connection.src] = connection
                    self.brain.connections.append(connection)

            if symbol[INDEX_SYMBOL] == Alphabet.ADD_EDGE:
                if (self.inputs_stack[-1].id, self.outputs_stack[-1].id) not in self.edges.keys():
                    connection = Connection()
                    connection.src = self.inputs_stack[-1].id
                    connection.dst = self.outputs_stack[-1].id
                    connection.weight = float(symbol[INDEX_PARAMS][0])
                    self.edges[connection.src, connection.dst] = connection
                    self.brain.connections.append(connection)
                    self.inputs_stack[-1].output_nodes.append(self.outputs_stack[-1])
                    self.outputs_stack[-1].input_nodes.append(self.inputs_stack[-1])
