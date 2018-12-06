from __future__ import absolute_import

from revolve.spec import BodyImplementation
from revolve.spec import NeuralNetImplementation
from revolve.spec import PartSpec
from revolve.spec import NeuronSpec

from revolve.spec.msgs import Robot
from revolve.spec.msgs import BodyPart
from revolve.spec.msgs import NeuralConnection
from revolve.spec.msgs import BodyConnection

from revolve.spec.exception import err


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
            err("Duplicate part ID '{}'".format(part.id))

        self.part_slots[part.id] = set()

        spec = self.spec.get(part.type)
        if spec is None:
            err("Unregistered part type '{}'".format(part.type))

        if dst_slot is not None:
            if dst_slot < 0 or dst_slot >= spec.arity:
                err("Part '{}' of type '{}' does not have destination slot {}"
                    .format(part.id, part.type, dst_slot))

            # At this point there are no connections to this
            # part yet, so we need only add the slot.
            self.part_slots[part.id].add(dst_slot)

        if len(part.param) != spec.n_parameters:
            err("Expecting {} parameters for part '{}', got {}."
                .format(spec.n_parameters, part.id, len(part.param)))

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
            err("Part '{}' of type '{}' does not have source slot {}"
                .format(parent.id, parent.type, conn.src))

        slots = self.part_slots[parent.id]
        if conn.src in slots:
            err("Trying to attach to already occupied slot {} of part '{}'"
                .format(conn.src, parent.id))

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

        missing_neurons = list(self.expected_neurons.keys())
        if len(missing_neurons):
            err("Missing expected neurons: {}"
                .format(', '.join(missing_neurons)))

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
                neuron_id = "{}-{}-{}".format(part.id, cat, i)
                self.expected_neurons[neuron_id] = "{}put".format(cat)

    def _process_neuron(self, neuron):
        """
        :param neuron:
        :type neuron: NeuronSpec
        :return:
        """
        if neuron.id in self.neurons:
            err("Duplicate neuron ID '{}'".format(neuron.id))

        self.neurons[neuron.id] = neuron.layer
        self.neural_connections[neuron.id] = set()

        if neuron.id in self.expected_neurons:
            layer = self.expected_neurons[neuron.id]
            if layer != neuron.layer:
                err("Neuron '{}' should be in layer '{}' instead of '{}'"
                    .format(neuron.id, layer, neuron.layer))

            if not neuron.HasField("partId"):
                err("Neuron '{}' in layer '{}' should have a part ID."
                    .format(neuron.id, layer))

            if neuron.partId not in self.parts:
                err("Unknown part ID '{}' for neuron '{}'."
                    .format(neuron.partId, neuron.id))

            del self.expected_neurons[neuron.id]

        spec = self.spec.get(neuron.type)
        if spec is None:
            err("Unspecified neuron type '{}'.".format(neuron.type))

        if neuron.layer not in spec.layers:
            err("Neuron of type '{}' is not allowed to be in layer '{}'."
                .format(neuron.type, neuron.layer))

        if spec.n_parameters != len(neuron.param):
            err("Expecting {} parameters for neuron '{}', got {}."
                .format(spec.n_parameters, neuron.id, len(neuron.param)))

    def _process_neural_connection(self, conn):
        """
        :param conn:
        :type conn: NeuralConnection
        :return:
        """
        if conn.src not in self.neurons:
            err("Unknown source neuron '{}'.".format(conn.src))

        if conn.dst not in self.neurons:
            err("Unknown destination neuron '{}'.".format(conn.dat))

        if self.neurons[conn.dst] == "input":
            err("Destination neuron '{}' is an input neuron.".format(conn.dst))

        connections = self.neural_connections[conn.src]
        if conn.dst in connections:
            err("Duplicate neural connection {} -> {}"
                .format(conn.src, conn.dst))

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
        self.brain_validator = NeuralNetValidator(
                spec=nn_spec,
                body_spec=body_spec,
                body=robot.body,
                brain=robot.brain)

    def validate(self):
        """
        Validates the robot.
        """
        self.body_validator.validate()
        self.brain_validator.validate()
