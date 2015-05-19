from ..spec.protobuf import Robot, BodyPart, NeuralConnection, BodyConnection
from ..spec import BodyImplementation, NeuralNetImplementation, PartSpec, NeuronSpec
from ..spec.exception import err


class Validator(object):
    """
    Validator class interface
    """
    def validate(self):
        """
        Validate method, should raise exceptions when errors
        are found.
        """
        raise NotImplementedError("Interface method.")


class BodyValidator(Validator):
    """
    Validates the basic structure of the given robot body.
    """
    def __init__(self, spec, body):
        """
        :param spec:
        :type spec: BodyImplementation
        :param body:
        :type body: Body
        """
        self.spec = spec
        self.body = body
        self.part_slots = {}

    def _process_body_part(self, part, dst_slot=None):
        """
        :param part:
        :return:
        """
        if part.id in self.part_slots:
            err("Duplicate part ID '%s'" % part.id)

        self.part_slots[part.id] = set()

        spec = self.spec.get(part.type)
        if spec is None:
            err("Unregistered part type '%s'" % part.type)

        if dst_slot is not None:
            if dst_slot < 0 or dst_slot >= spec.arity:
                err("Part '%s' of type '%s' does not have destination slot %d" %
                    (part.id, part.type, dst_slot))

            # At this point there are no connections to this
            # part yet, so we need only add the slot.
            self.part_slots[part.id].add(dst_slot)

        if len(part.param) != spec.n_parameters:
            err("Expecting %d parameters for part '%s', got %d." %
                (spec.n_parameters, part.id, len(part.param)))

        if not spec.params_validate(part.param):
            err("Invalid parameter length or ranges.")

        for conn in part.child:
            self._process_body_connection(part, spec, conn)

    def _process_body_connection(self, parent, spec, conn):
        """
        :param parent:
        :type parent: BodyPart
        :param spec:
        :type spec: PartSpec
        :param conn:
        :type conn: BodyConnection
        :return:
        """
        if conn.src < 0 or conn.src >= spec.arity:
            err("Part '%s' of type '%s' does not have source slot %d" %
                (parent.id, parent.type, conn.src))

        slots = self.part_slots[parent.id]
        if conn.src in slots:
            err("Trying to attach to already occupied slot %d of part '%s'"
                % (conn.src, parent.id))

        slots.add(conn.src)
        self._process_body_part(conn.part, conn.dst)

    def validate(self):
        """
        Validates the robot body.
        """
        # Start processing at body root
        self._process_body_part(self.body.root)


class NeuralNetValidator(Validator):
    """
    Validates a neural net against a spec -
    this requires knowledge of the body as well.
    """

    def __init__(self, spec, body_spec, body, brain):
        """
        :param spec:
        :type spec: NeuralNetImplementation
        :param body_spec:
        :type spec: BodyImplementation
        :param body:
        :param brain:
        """
        self.spec = spec
        self.body_spec = body_spec
        self.body = body
        self.brain = brain

        self.expected_neurons = {}
        self.neurons = {}
        self.neural_connections = {}
        self.parts = set()

    def validate(self):
        """
        Validates the neural network, raises exceptions
        of something's wrong.
        """
        # Process body parts to get expected neurons, this
        # should not raise any errors.
        self._process_body_part(self.body.root)

        for neuron in self.brain.neuron:
            self._process_neuron(neuron)

        for conn in self.brain.connection:
            self._process_neural_connection(conn)

        missing_neurons = self.expected_neurons.keys()
        if len(missing_neurons):
            err("Missing expected neurons: %s" % ', '.join(missing_neurons))

    def _process_body_part(self, part):
        """
        Process body parts to get expected neurons.
        :param part:
        :return:
        """
        self.parts.add(part.id)
        spec = self.body_spec.get(part.type)

        for conn in part.child:
            self._process_body_part(conn.part)

        cats = {"in": spec.inputs, "out": spec.outputs}
        for cat in cats:
            for i in range(cats[cat]):
                neuron_id = "%s-%s-%d" % (part.id, cat, i)
                self.expected_neurons[neuron_id] = "%sput" % cat

    def _process_neuron(self, neuron):
        """
        :param neuron:
        :type neuron: NeuronSpec
        :return:
        """
        if neuron.id in self.neurons:
            err("Duplicate neuron ID '%s'" % neuron.id)

        self.neurons[neuron.id] = neuron.layer
        self.neural_connections[neuron.id] = set()

        if neuron.id in self.expected_neurons:
            layer = self.expected_neurons[neuron.id]
            if layer != neuron.layer:
                err("Neuron '%s' should be in layer '%s' instead of '%s'" %
                    (neuron.id, layer, neuron.layer))

            if not neuron.HasField("partId"):
                err("Neuron '%s' in layer '%s' should have a part ID." % (neuron.id, layer))

            if neuron.partId not in self.parts:
                err("Unknown part ID '%s' for neuron '%s'." % (neuron.partId, neuron.id))

            del self.expected_neurons[neuron.id]

        spec = self.spec.get(neuron.type)
        if spec is None:
            err("Unspecified neuron type '%s'." % neuron.type)

        if neuron.layer not in spec.layers:
            err("Neuron of type '%s' is not allowed to be in layer '%s'." % (neuron.type, neuron.layer))

        if spec.n_parameters != len(neuron.param):
            err("Expecting %d parameters for neuron '%s', got %d." %
                (spec.n_parameters, neuron.id, len(neuron.param)))

    def _process_neural_connection(self, conn):
        """
        :param conn:
        :type conn: NeuralConnection
        :return:
        """
        if conn.src not in self.neurons:
            err("Unknown source neuron '%s'." % conn.src)

        if conn.dst not in self.neurons:
            err("Unknown destination neuron '%s'." % conn.dat)

        if self.neurons[conn.dst] == "input":
            err("Destination neuron '%s' is an input neuron." % conn.dst)

        connections = self.neural_connections[conn.src]
        if conn.dst in connections:
            err("Duplicate neural connection %s -> %s" % (conn.src, conn.dst))

        connections.add(conn.dst)


class RobotValidator(Validator):
    """
    Validator for the default robot, with standard body spec
    and neural net.
    """
    def __init__(self, robot, body_spec, nn_spec):
        """
        :param robot:
        :type robot: Robot
        :param body_spec:
        :type body_spec: BodyImplementation
        :param nn_spec:
        :type nn_spec: NeuralNetImplementation
        :return:
        """
        self.body_validator = BodyValidator(body_spec, robot.body)
        self.brain_validator = NeuralNetValidator(nn_spec, body_spec, robot.body, robot.brain)

    def validate(self):
        """
        Validates the robot.
        """
        self.body_validator.validate()
        self.brain_validator.validate()