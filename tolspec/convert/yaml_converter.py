import yaml
from ..tol_pb2 import *
from ..implementation import SpecImplementation, Part, Neuron
from .exception import err


class YamlToProtobuf:
    """
    Takes the ToL YAML format and creates from it
    a Protobuf implementation.
    """

    def __init__(self, spec, lines):
        """
        :param spec:
        :type spec: SpecImplementation
        :param lines:
        :type lines: iterable
        :return:
        """
        # TODO If at all necessary optimize this
        contents = '\n'.join([l for l in lines])
        obj = yaml.load(contents)
        self.spec = spec

        self.part_ids = set()
        self.robot = Robot()

        self.robot.id = obj.get('id', 0)

        if 'body' not in obj:
            err("Missing robot body.")

        self.neurons = {}
        self.robot.body.root.CopyFrom(self._process_body_part(obj['body']))

        brain = obj.get('brain', {})
        neurons = brain.get('neurons', [])
        params = brain.get('params', {})
        connections = brain.get('connections', [])

        self._create_hidden_neurons(neurons)

        # Process given parameters
        for neuron_id in params:
            self._process_neuron_params(neuron_id, params[neuron_id])

        self._process_neurons()
        self._create_neuron_connections(connections)

    def get_protobuf(self):
        """
        Returns the generated protobuf robot.
        :return:
        :rtype: Robot
        """
        return self.robot

    def _process_body_part(self, conf, dst_slot=None):
        """
        :param conf:
        :return:
        :rtype: BodyPart
        """
        part = BodyPart()

        if 'id' not in conf:
            err("Missing part ID.")

        part_id = conf['id']
        if part_id in self.part_ids:
            err("Duplicate part ID '%s'" % part_id)
        self.part_ids.add(part_id)

        if 'type' not in conf:
            err("Missing part type.")
        part_type = conf['type']

        spec = self.spec.get_part(part_type)
        if spec is None:
            err("Part type '%s' not in implementation spec." % part_type)

        # Check destination slot arity
        if dst_slot is not None and dst_slot >= spec.arity:
            err("Cannot attach part '%s' with arity %d at slot %d" %
                (part_id, spec.arity, dst_slot))

        # Add part parameters
        part.orientation = conf.get('orientation', 0)
        params = spec.serialize_params(conf.get('params', {}))
        for param in params:
            p = part.param.add()
            p.value = param

        # Add children
        children = conf.get('children', {})
        for src in children:
            if src >= spec.arity:
                err("Cannot attach to slot %d of part '%s' with arity %d." %
                    (src, part_id, spec.arity))

            if src == dst_slot:
                err("Part '%s': Attempt to use slot %d for child which is already "
                    "attached to parent." % (part_id, src))
            self._process_body_connection(part, src, children[src])

        # Add automatic input / output neurons
        cats = {"in": spec.input_neurons, "out": spec.output_neurons}
        for cat in cats:
            for i in range(cats[cat]):
                neuron_id = "%s-%s-%d" % (part_id, cat, i)
                if neuron_id in self.neurons:
                    err("Duplicate neuron ID '%s'" % neuron_id)

                self.neurons[neuron_id] = {
                    "layer": "%sput" % cat,
                    "type": "simple"
                }

                self._process_neuron_params(neuron_id, {})

        return part

    def _process_body_connection(self, part, src, conf):
        """
        :param part:
        :type part: BodyPart
        :param src: Slot on parent
        :type src: int
        :param conf:
        :return:
        :rtype: BodyConnection
        """
        conn = part.child.add()
        conn.src = src
        conn.dst = conf['slot'] if 'slot' in conf else 0
        conn.part = self._process_body_part(conf, conn.dst)

    def _create_hidden_neurons(self, neurons):
        """
        Creates hidden neurons.
        :return:
        """
        for neuron_id in neurons:
            if neuron_id in self.neurons:
                err("Duplicate neuron ID '%s'" % neuron_id)

            self.neurons[neuron_id] = {
                "layer": "hidden",
                "type": "simple"
            }

            self._process_neuron_params(neuron_id, neurons[neuron_id])

    def _process_neuron_params(self, neuron_id, conf):
        """
        Processes params for a single neuron.
        :param neuron_id:
        :param conf:
        :return:
        """
        if neuron_id not in self.neurons:
            err("Cannot set parameters for unknown neuron '%s'" % neuron_id)

        current = self.neurons[neuron_id]
        current["type"] = conf.get("type", "Simple")

        if current["type"] != "Simple" and current["layer"] == "input":
            err("Input neuron '%s' must be of type 'Simple'" % neuron_id)

        spec = self.spec.get_neuron(current["type"])

        if spec is None:
            err("Unknown neuron type '%s'" % current["type"])

        current["params"] = spec.serialize_params(conf)

    def _process_neurons(self):
        """
        Processes neuron data into protobuf neurons.
        :return:
        """
        for neuron_id in self.neurons:
            conf = self.neurons[neuron_id]
            neuron = self.robot.brain.neuron.add()
            neuron.id = neuron_id
            neuron.layer = conf["layer"]
            neuron.type = conf["type"]

            for value in conf["params"]:
                param = neuron.param.add()
                param.value = value

    def _create_neuron_connections(self, connections):
        """
        Creates connections from the robot connection list.
        :param connections:
        :return:
        """
        for conn in connections:
            c = self.robot.brain.connection.add()
            src = conn.get("src", None)
            dst = conn.get("dst", None)
            c.weight = conn.get("weight", 0)

            if src is None:
                err("Neuron connection is missing 'src'.")

            if src not in self.neurons:
                err("Using unknown neuron '%s' as connection source." % src)

            if dst is None:
                err("Neuron connection is missing 'dst'.")

            if dst not in self.neurons:
                err("Using unknown neuron '%s' as connection destination." % dst)

            if self.neurons[dst]["layer"] == "input":
                err("Using input neuron '%s' as destination." % dst)

            c.src = src
            c.dst = dst
