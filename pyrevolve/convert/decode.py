from __future__ import absolute_import

from ..spec import BodyImplementation, NeuralNetImplementation
from ..spec.msgs import Body, BodyPart, NeuralNetwork
from ..spec.exception import err


class BodyDecoder(object):
    """
    Body decoder for the default YAML object structure
    """

    def __init__(self, spec):
        """
        :param spec:
        :type spec: BodyImplementation
        :return:
        """
        self.spec = spec
        self.part_ids = set()

    def decode(self, obj):
        """
        :param obj:
        :return:
        """
        if 'body' not in obj:
            err("Missing robot body.")

        body = Body()
        body.root.CopyFrom(self._process_body_part(obj['body']))
        return body

    def _process_body_part(self, part, dst_slot=None):
        """
        :param part:
        :return:
        :rtype: BodyPart
        """
        proto_part = BodyPart()

        if 'id' not in part:
            err("Missing part ID.")

        proto_part.id = part_id = part['id']
        if part_id in self.part_ids:
            err("Duplicate part ID '{}'".format(part_id))
        self.part_ids.add(part_id)

        if 'type' not in part:
            err("Missing part type.")
        proto_part.type = part_type = part['type']

        proto_template = self.spec.get(part_type)
        if proto_template is None:
            err("Part type '{}' not in implementation spec.".format(part_type))

        # Check destination slot arity
        if dst_slot is not None and dst_slot >= proto_template.arity:
            err("Cannot attach part '%s' with arity %d at slot %d" %
                (part_id, proto_template.arity, dst_slot))

        # Add part parameters
        proto_part.orientation = part.get('orientation', 0)

        params = proto_template.serialize_params(part.get('params', {}))
        for param in params:
            p = proto_part.param.add()
            p.value = param

        # Add children
        children = part.get('children', {})
        for src in children:
            if src >= proto_template.arity:
                err("Cannot attach to slot {} of part '{}' with arity "
                    "{}.".format(src, part_id, proto_template.arity))

            if src == dst_slot:
                err("Part '{}': Attempt to use slot {} for child which is "
                    "already attached to parent.".format(part_id, src))
            self._process_body_connection(proto_part, src, children[src])

        return proto_part

    def _process_body_connection(self, parent_part, src_slot, child_part):
        """
        :param parent_part:
        :type parent_part: BodyPart
        :param src_slot: Slot on parent
        :type src_slot: int
        :param child_part:
        :return:
        :rtype: BodyConnection
        """
        conn = parent_part.child.add()
        conn.src_slot = src_slot
        conn.dst_slot = child_part['slot'] if 'slot' in child_part else 0
        conn.part.CopyFrom(self._process_body_part(child_part, conn.dst_slot))


class NeuralNetworkDecoder(object):
    """
    Decoder class for the standard neural network spec.
    """

    def __init__(self, spec, body_spec):
        """
        :param spec:
        :type spec: NeuralNetImplementation
        :param body_spec:
        :type body_spec: BodyImplementation
        :return:
        """
        self.spec = spec
        self.body_spec = body_spec
        self.neurons = {}

    def decode(self, obj):
        """
        :param obj:
        :return:
        :rtype: NeuralNetwork
        """
        if 'body' not in obj:
            err("Robot body required for standard Neural Network decode.")

        # Prepare all automatic input / output neurons
        self._process_body_part(obj['body'])

        brain = obj.get('brain', {})
        neurons = brain.get('neurons', [])
        params = brain.get('params', {})
        connections = brain.get('connections', [])

        self._create_hidden_neurons(neurons)

        # Process given parameters
        for neuron_id in params:
            self._process_neuron_params(neuron_id, params[neuron_id])

        nn = NeuralNetwork()
        self._process_neurons(nn)
        self._create_neuron_connections(connections, nn)

        return nn

    def _process_body_part(self, conf):
        """
        :param conf:
        :return:
        :rtype: BodyPart
        """
        part_id = conf['id']
        part_type = conf['type']

        spec = self.body_spec.get(part_type)
        if spec is None:
            err("Part type '{}' not in implementation spec.".format(part_type))

        # Add children
        children = conf.get('children', {})
        for src in children:
            self._process_body_part(children[src])

        # Add automatic input / output neurons
        cats = {"in": spec.inputs, "out": spec.outputs}
        for cat in cats:
            default_type = "Input" if cat == "in" else "Simple"

            for i in range(cats[cat]):
                neuron_id = "{}-{}-{}".format(part_id, cat, i)
                if neuron_id in self.neurons:
                    err("Duplicate neuron ID '{}'".format(neuron_id))

                self.neurons[neuron_id] = {
                    "layer": "{}put".format(cat),
                    "part_id": part_id
                }

                self._process_neuron_params(neuron_id, {"type": default_type})

    def _process_neuron_params(self, neuron_id, conf):
        """
        Processes params for a single neuron.
        :param neuron_id:
        :param conf:
        :return:
        """
        if neuron_id not in self.neurons:
            err("Cannot set parameters for unknown neuron '{}'".format(
                    neuron_id))

        current = self.neurons[neuron_id]
        if "type" not in current or "type" in conf:
            current["type"] = conf.get("type", "Simple")

        if current["type"] != "Input" and current["layer"] == "input":
            err("Input neuron '{}' must be of type 'Input'".format(neuron_id))

        spec = self.spec.get(current["type"])
        if spec is None:
            err("Unknown neuron type '{}'".format(current["type"]))

        current["params"] = spec.serialize_params(conf)

    def _create_hidden_neurons(self, neurons):
        """
        Creates hidden neurons.
        :return:
        """
        for n_id in neurons:
            if n_id in self.neurons:
                err("Duplicate neuron ID '{}'".format(n_id))

            # This sets the defaults, the accurate values - if present - will
            # be set by `_process_neuron_params`.
            self.neurons[n_id] = {
                "layer": "hidden",
                "type": "Simple"
            }

            if "part_id" in neurons[n_id]:
                self.neurons[n_id]["part_id"] = neurons[n_id]["part_id"]

            self._process_neuron_params(n_id, neurons[n_id])

    def _create_neuron_connections(self, connections, brain):
        """
        Creates connections from the robot connection list.
        :param connections:
        :param brain:
        :return:
        """
        for conn in connections:
            c = brain.connection.add()
            src = conn.get("src", None)
            dst = conn.get("dst", None)
            c.weight = conn.get("weight", 0)

            if src is None:
                err("Neuron connection is missing 'src'.")

            if src not in self.neurons:
                err("Using unknown neuron '{}' as connection source.".format(
                        src))

            if dst is None:
                err("Neuron connection is missing 'dst'.")

            if dst not in self.neurons:
                err("Using unknown neuron '{}' as connection "
                    "destination.".format(dst))

            if self.neurons[dst]["layer"] == "input":
                err("Using input neuron '{}' as destination.".format(dst))

            c.src = src
            c.dst = dst

    def _process_neurons(self, brain):
        """
        Processes neuron data into protobuf neurons.
        :param brain:
        :type brain: NeuralNetwork
        :return:
        """
        for neuron_id in self.neurons:
            conf = self.neurons[neuron_id]
            neuron = brain.neuron.add()
            neuron.id = neuron_id
            neuron.layer = conf["layer"]
            neuron.type = conf["type"]

            if "part_id" in conf:
                neuron.partId = conf["part_id"]

            for value in conf["params"]:
                param = neuron.param.add()
                param.value = value
