from pyrevolve.genotype.plasticoding.alphabet import Alphabet, INDEX_SYMBOL, INDEX_PARAMS
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.brain import BrainNN
from pyrevolve.revolve_bot.brain.brain_nn import Connection, Node, Params
from pyrevolve.revolve_bot.revolve_module import Orientation, CoreModule, BrickModule, ActiveHingeModule, \
    TouchSensorModule, LinearActuatorModule


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
                if symbol in Alphabet.modules(self._conf.allow_vertical_brick,self._conf.allow_linear_joint):
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

    class Cursor:
        def __init__(self, current_module, orientation):
            self.module = current_module
            self.orientation = orientation  # degrees
            self.history = [current_module]

        def copy(self):
            # deepcopy is an overkill here and probably even armful
            copy = PlasticodingDecoder.Cursor(self.module, self.orientation)
            copy.history = self.history.copy()
            return copy

    class CursorStack:
        def __init__(self, starting_module, orientation=0):
            self._stack = [
                PlasticodingDecoder.Cursor(starting_module, orientation)
            ]

        def pop(self):
            if len(self._stack) > 1:
                self._stack.pop()

        def push(self):
            self._stack.append(
                self.current.copy()
            )

        @property
        def current(self):
            return self._stack[-1]

        @property
        def history(self):
            return self.current.history

        def save_history(self):
            self.current.history.append(self.current.module)

        def pop_history(self):
            assert(len(self.current.history) > 0)
            self.current.module = self.current.history[-1]
            self.current.history.pop()

        def empty(self):
            return len(self._stack) == 0

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

        self.stack = None
        self.morph_mounting_container = None
        self.quantity_modules = 1
        self.quantity_nodes = 0
        self.inputs_stack = []
        self.outputs_stack = []
        self.edges = {}

    def decode_sentence(self):
        self.body._id = self._id

        core_module = CoreModule()
        self.body._body = core_module
        core_module.id = str(self.quantity_modules)
        core_module.info = {
            'orientation': Orientation.FORWARD,
            'new_module_type': Alphabet.CORE_COMPONENT
        }
        core_module.rgb = [1, 1, 0]
        self.stack = PlasticodingDecoder.CursorStack(core_module, orientation=0)

        for word in self._command_sentence[1:]:
            symbol = word[INDEX_SYMBOL]

            if symbol in Alphabet.morphology_mounting_commands():
                self.morph_mounting_container = symbol

            elif symbol in Alphabet.modules(self._conf.allow_vertical_brick, self._conf.allow_linear_joint):
                if self.morph_mounting_container is not None \
                        and symbol is not Alphabet.CORE_COMPONENT:

                    if type(self.stack.current.module) == CoreModule \
                            or type(self.stack.current.module) == BrickModule:
                        slot = self.get_slot(self.morph_mounting_container).value
                    elif type(self.stack.current.module) == ActiveHingeModule:
                        slot = Orientation.FORWARD.value
                    elif self._conf.allow_linear_joint:
                        if type(self.stack.current.module) == LinearActuatorModule:
                            slot = Orientation.FORWARD.value
                    else:
                        raise RuntimeError(
                            f'Mounting reference {type(self.stack.current.module)} does not support a mount')

                    if self.quantity_modules < self._conf.max_structural_modules:
                        self.new_module(slot, symbol, word, self._conf.allow_joint_joint_attachment)

            elif symbol in Alphabet.morphology_moving_commands(self._conf.use_movement_commands,
                                                               self._conf.use_rotation_commands,
                                                               self._conf.use_movement_stack):
                self.move_in_body(word)

            elif symbol in Alphabet.controller_changing_commands():
                self.decode_brain_changing(word)

            elif symbol in Alphabet.controller_moving_commands():
                self.decode_brain_moving(word)

            else:
                raise RuntimeError(f'Unrecognized symbol: {symbol}')

        self.add_imu_nodes()

        self.body._brain = self.brain
        return self.body

    @staticmethod
    def get_slot(morph_mounting_container):
        slot = None
        if morph_mounting_container == Alphabet.ADD_FRONT:
            slot = Orientation.FORWARD
        elif morph_mounting_container == Alphabet.ADD_LEFT:
            slot = Orientation.LEFT
        elif morph_mounting_container == Alphabet.ADD_RIGHT:
            slot = Orientation.RIGHT
        return slot

    def get_angle(self, new_module_type, parent):
        if self._conf.use_rotation_commands:
            pending_rotation = self.stack.current.orientation
            parent_orientation = parent.orientation if parent.orientation is not None else 0
            return parent_orientation + pending_rotation
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

    def move_in_body(self, word):
        symbol = word[INDEX_SYMBOL]
        if symbol == Alphabet.PUSH_MOV_STACK:
            self.stack.push()

        elif symbol == Alphabet.POP_MOV_STACK:
            self.stack.pop()

        elif symbol == Alphabet.MOVE_BACK:
            if len(self.stack.history) > 0:
                self.stack.pop_history()

        elif symbol == Alphabet.MOVE_FRONT:
            if self.stack.current.module.children[Orientation.FORWARD.value] is not None \
                    and type(self.stack.current.module.children[Orientation.FORWARD.value]) is not TouchSensorModule:
                self.stack.save_history()
                self.stack.current.module = self.stack.current.module.children[Orientation.FORWARD.value]

        elif symbol == Alphabet.MOVE_RIGHT or symbol == Alphabet.MOVE_LEFT:

            if symbol == Alphabet.MOVE_LEFT and type(self.stack.current.module) is not ActiveHingeModule \
                    and type(self.stack.current.module) is not LinearActuatorModule \
                    and self.stack.current.module.children[Orientation.LEFT.value] is not None \
                    and type(self.stack.current.module.children[Orientation.LEFT.value]) is not TouchSensorModule:
                self.stack.save_history()
                self.stack.current.module = self.stack.current.module.children[Orientation.LEFT.value]

            elif symbol == Alphabet.MOVE_RIGHT and type(self.stack.current.module) is not ActiveHingeModule \
                    and type(self.stack.current.module) is not LinearActuatorModule \
                    and self.stack.current.module.children[Orientation.RIGHT.value] is not None \
                    and type(self.stack.current.module.children[Orientation.RIGHT.value]) is not TouchSensorModule:
                self.stack.save_history()
                self.stack.current.module = self.stack.current.module.children[Orientation.RIGHT.value]

            if (type(self.stack.current.module) is ActiveHingeModule or type(self.stack.current.module) is LinearActuatorModule) \
                    and self.stack.current.module.children[Orientation.FORWARD.value] is not None:
                self.stack.save_history()
                self.stack.current.module = self.stack.current.module.children[Orientation.FORWARD.value]

        elif symbol is Alphabet.ROTATE_90 or symbol is Alphabet.ROTATE_N90:
            self.stack.current.orientation += 90 if symbol is Alphabet.ROTATE_90 else -90

        else:
            raise RuntimeError(f'movement command not recognized {symbol}')

    def new_module(self, slot, new_module_type: Alphabet, word, allow_joint_joint_attachment: bool):
        mount = False
        if self.stack.current.module.children[slot] is None:
            mount = True
            if new_module_type == Alphabet.SENSOR \
                    and (type(self.stack.current.module) is ActiveHingeModule or type(self.stack.current.module) is LinearActuatorModule):
                mount = False
            elif not allow_joint_joint_attachment \
                    and (type(self.stack.current.module) is ActiveHingeModule or type(self.stack.current.module) is LinearActuatorModule) \
                    and new_module_type.is_joint():
                mount = False

        if type(self.stack.current.module) is CoreModule \
                and self.stack.current.module.children[1] is not None \
                and self.stack.current.module.children[2] is not None \
                and self.stack.current.module.children[3] is not None \
                and self.stack.current.module.children[0] is None:
            slot = 0
            mount = True

        if not mount:
            return

        if new_module_type == Alphabet.BLOCK \
                or new_module_type == Alphabet.BLOCK_VERTICAL:
            module = BrickModule()
        elif new_module_type == Alphabet.JOINT_VERTICAL \
                or new_module_type == Alphabet.JOINT_HORIZONTAL:
            module = ActiveHingeModule()
        elif new_module_type == Alphabet.LINEAR_JOINT:
            module = LinearActuatorModule()
        elif new_module_type == Alphabet.SENSOR:
            module = TouchSensorModule()
        else:
            raise NotImplementedError(f'{new_module_type}')

        module.info = {'new_module_type': new_module_type}
        module.orientation = self.get_angle(new_module_type, self.stack.current.module)
        module.rgb = self.get_color(new_module_type)

        if new_module_type != Alphabet.SENSOR:
            try:
                self.quantity_modules += 1
                module.id = str(self.quantity_modules)
                self.stack.current.module.children[slot] = module
                # RevolveBot.ItersectionCollisionException can be thrown at this line
                self.check_intersection(self.stack.current.module, slot, module)
                self.morph_mounting_container = None
                self.stack.save_history()
                self.stack.current.module = module
                if new_module_type == Alphabet.JOINT_HORIZONTAL \
                        or new_module_type == Alphabet.JOINT_VERTICAL:
                    self.decode_brain_node(word, module.id)
            except RevolveBot.ItersectionCollisionException:
                self.stack.current.module.children[slot] = None
                self.quantity_modules -= 1
        else:
            self.stack.current.module.children[slot] = module
            self.morph_mounting_container = None
            module.id = self.stack.current.module.id + 's' + str(slot)
            self.decode_brain_node(word, module.id)

    def check_intersection(self, parent, slot, module):
        """
        Update coordinates of module, raises exception if there is two blocks have the same coordinates.
        :raises: RevolveBot.ItersectionCollisionException if there was a collision in the robot tree
        """
        dic = {Orientation.FORWARD.value: 0,
               Orientation.LEFT.value: 1,
               Orientation.BACK.value: 2,
               Orientation.RIGHT.value: 3}

        inverse_dic = {0: Orientation.FORWARD.value,
                       1: Orientation.LEFT.value,
                       2: Orientation.BACK.value,
                       3: Orientation.RIGHT.value}

        # TODO remove orientation, should be useless now
        direction = dic[parent.info['orientation'].value] + dic[slot]
        direction = direction % len(dic)
        new_direction = Orientation(inverse_dic[direction])
        module.info['orientation'] = new_direction

        # Generate coordinate for block, could throw exception
        self.body.update_substrate(raise_for_intersections=True)

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

    def decode_brain_moving(self, word):
        symbol = word[INDEX_SYMBOL]

        # if there is at least both one sensor and one oscillator
        if len(self.outputs_stack) > 0 and len(self.inputs_stack) > 0:

            intermediate = int(float(word[INDEX_PARAMS][0]))
            sibling = int(float(word[INDEX_PARAMS][1]))

            if symbol == Alphabet.MOVE_REF_S:

                if len(self.inputs_stack[-1].output_nodes) < intermediate:
                    intermediate = len(self.inputs_stack[-1].output_nodes) - 1
                else:
                    intermediate = intermediate - 1

                if len(self.inputs_stack[-1].output_nodes[intermediate].input_nodes) < sibling:
                    sibling = len(self.inputs_stack[-1].output_nodes[intermediate].input_nodes) - 1
                else:
                    sibling = sibling - 1

                self.inputs_stack[-1] = self.inputs_stack[-1].output_nodes[intermediate].input_nodes[sibling]

            if symbol == Alphabet.MOVE_REF_O:

                if len(self.outputs_stack[-1].input_nodes) < intermediate:
                    intermediate = len(self.outputs_stack[-1].input_nodes) - 1
                else:
                    intermediate = intermediate - 1

                if len(self.outputs_stack[-1].input_nodes[intermediate].output_nodes) < sibling:
                    sibling = len(self.outputs_stack[-1].input_nodes[intermediate].output_nodes) - 1
                else:
                    sibling = sibling - 1

                self.outputs_stack[-1] = self.outputs_stack[-1].input_nodes[intermediate].output_nodes[sibling]

    def decode_brain_changing(self, word):
        symbol = word[INDEX_SYMBOL]
        conf = self._conf

        # if there is at least both one oscillator
        if len(self.outputs_stack) > 0:

            if symbol == Alphabet.MUTATE_PER:
                self.outputs_stack[-1].params.period += float(word[INDEX_PARAMS][0])
                if self.outputs_stack[-1].params.period > conf.oscillator_param_max:
                    self.outputs_stack[-1].params.period = conf.oscillator_param_max
                if self.outputs_stack[-1].params.period < conf.oscillator_param_min:
                    self.outputs_stack[-1].params.period = conf.oscillator_param_min

            if symbol == Alphabet.MUTATE_AMP:
                self.outputs_stack[-1].params.amplitude += float(word[INDEX_PARAMS][0])
                if self.outputs_stack[-1].params.amplitude > conf.oscillator_param_max:
                    self.outputs_stack[-1].params.amplitude = conf.oscillator_param_max
                if self.outputs_stack[-1].params.amplitude < conf.oscillator_param_min:
                    self.outputs_stack[-1].params.amplitude = conf.oscillator_param_min

            if symbol == Alphabet.MUTATE_OFF:
                self.outputs_stack[-1].params.phase_offset += float(word[INDEX_PARAMS][0])
                if self.outputs_stack[-1].params.phase_offset > conf.oscillator_param_max:
                    self.outputs_stack[-1].params.phase_offset = conf.oscillator_param_max
                if self.outputs_stack[-1].params.phase_offset < conf.oscillator_param_min:
                    self.outputs_stack[-1].params.phase_offset = conf.oscillator_param_min

        if symbol == Alphabet.MUTATE_EDGE:
            if len(self.edges) > 0:
                if (self.inputs_stack[-1].id, self.outputs_stack[-1].id) in self.edges.keys():
                    self.edges[self.inputs_stack[-1].id, self.outputs_stack[-1].id].weight \
                        += float(word[INDEX_PARAMS][0])
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
            if symbol == Alphabet.LOOP:

                if (self.outputs_stack[-1].id, self.outputs_stack[-1].id) not in self.edges.keys():
                    connection = Connection()
                    connection.src = self.outputs_stack[-1].id
                    connection.dst = connection.src
                    connection.weight = float(word[INDEX_PARAMS][0])
                    self.edges[connection.src, connection.src] = connection
                    self.brain.connections.append(connection)

            if symbol == Alphabet.ADD_EDGE:
                if (self.inputs_stack[-1].id, self.outputs_stack[-1].id) not in self.edges.keys():
                    connection = Connection()
                    connection.src = self.inputs_stack[-1].id
                    connection.dst = self.outputs_stack[-1].id
                    connection.weight = float(word[INDEX_PARAMS][0])
                    self.edges[connection.src, connection.dst] = connection
                    self.brain.connections.append(connection)
                    self.inputs_stack[-1].output_nodes.append(self.outputs_stack[-1])
                    self.outputs_stack[-1].input_nodes.append(self.inputs_stack[-1])
