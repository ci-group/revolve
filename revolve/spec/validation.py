from ..spec.protobuf import Robot, BodyPart, NeuralConnection, BodyConnection
from ..spec import SpecImplementation, PartSpec, NeuronSpec
from ..spec.exception import err


def validate_robot(spec, robot):
    """
    :param spec:
    :type spec: SpecImplementation
    :param robot:
    :type robot: Robot
    :return:
    """
    validator = SpecValidator(spec, robot)
    validator.validate()


class SpecValidator:
    """
    Validates a robot protobuf against a spec implementation.
    """

    def __init__(self, spec, robot):
        """

        :param spec:
        :type spec: SpecImplementation
        :param robot:
        :type robot: Robot
        :return:
        """
        self.spec = spec
        self.robot = robot

        self.part_slots = {}
        self.neurons = {}
        self.expected_neurons = {}
        self.neural_connections = {}

    def validate(self):
        """
        Validates the robot specification against the implementation,
        raises a RobotSpecificationException if an error occurs.
        :return:
        """
        self._process_body_part(self.robot.body.root)

        for neuron in self.robot.brain.neuron:
            self._process_neuron(neuron)

        for conn in self.robot.brain.connection:
            self._process_neural_connection(conn)

        missing_neurons = self.expected_neurons.keys()
        if len(missing_neurons):
            err("Missing expected neurons: %s" % ', '.join(missing_neurons))

    def _process_body_part(self, part, dst_slot=None):
        """

        :param part:
        :return:
        """
        if part.id in self.part_slots:
            err("Duplicate part ID '%s'" % part.id)

        self.part_slots[part.id] = set()

        spec = self.spec.get_part(part.type)
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

        cats = {"in": spec.input_neurons, "out": spec.output_neurons}
        for cat in cats:
            for i in range(cats[cat]):
                neuron_id = "%s-%s-%d" % (part.id, cat, i)
                self.expected_neurons[neuron_id] = "%sput" % cat

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

            if layer == "input" and neuron.type != "Simple":
                err("Input neuron '%s' should be of type 'Simple'" % neuron.id)

            if not neuron.HasField("partId"):
                err("Neuron '%s' in layer '%s' should have a part ID." % (neuron.id, layer))

            if neuron.partId not in self.part_slots:
                err("Unknown part ID '%s' for neuron '%s'." % (neuron.partId, neuron.id))

            del self.expected_neurons[neuron.id]

        spec = self.spec.get_neuron(neuron.type)
        if spec is None:
            err("Unspecified neuron type '%s'." % neuron.type)

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