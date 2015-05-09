"""
Sample
"""
from __future__ import absolute_import
import yaml
from ..spec import BodyImplementation, NeuralNetImplementation
from ..spec.protobuf import *
from ..spec.exception import err


def yaml_to_robot(body_spec, nn_spec, yaml):
    """
    :param body_spec:
    :type body_spec: BodyImplementation
    :param nn_spec:
    :type nn_spec: NeuralNetImplementation
    :param yaml:
    :type yaml: stream
    :return:
    """
    obj = YamlToRobot(body_spec, nn_spec, yaml)
    return obj.get_protobuf()


class YamlToRobot:
    """
    Sample converter creates a Robot protobuf message
    from a YAML stream and a body / neural net spec.
    """

    def __init__(self, body_spec, nn_spec, stream):
        """
        :param body_spec:
        :type body_spec: BodyImplementation
        :param stream:
        :type stream: stream
        :return:
        """
        obj = yaml.load(stream)
        self.body_spec = body_spec
        self.nn_spec = nn_spec

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

        part.id = part_id = conf['id']
        if part_id in self.part_ids:
            err("Duplicate part ID '%s'" % part_id)
        self.part_ids.add(part_id)

        if 'type' not in conf:
            err("Missing part type.")
        part.type = part_type = conf['type']

        spec = self.body_spec.get(part_type)
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
        cats = {"in": spec.inputs, "out": spec.outputs}
        for cat in cats:
            for i in range(cats[cat]):
                neuron_id = "%s-%s-%d" % (part_id, cat, i)
                if neuron_id in self.neurons:
                    err("Duplicate neuron ID '%s'" % neuron_id)

                self.neurons[neuron_id] = {
                    "layer": "%sput" % cat,
                    "part_id": part.id
                }

                self._process_neuron_params(neuron_id, {"type": "Input"})

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
        conn.part.CopyFrom(self._process_body_part(conf, conn.dst))

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
                "type": "Simple"
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
        if "type" not in current or "type" in conf:
            current["type"] = conf.get("type", "Simple")

        if current["type"] != "Input" and current["layer"] == "input":
            err("Input neuron '%s' must be of type 'Input'" % neuron_id)

        spec = self.nn_spec.get(current["type"])
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

            if "part_id" in conf:
                neuron.partId = conf["part_id"]

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
