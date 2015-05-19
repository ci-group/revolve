"""
Random generator for the default neural network
"""
from __future__ import print_function
import random
import itertools
from ..spec import NeuralNetwork, Neuron, NeuralNetImplementation, NeuronSpec, Body, BodyImplementation


# Epsilon value below which neuron weights are discarded
EPSILON = 1e-11

def _extract_io(body_spec, part):
    spec = body_spec.get(part.type)
    inputs = ["%s-in-%d" % (part.id, i) for i in range(spec.inputs)]
    outputs = ["%s-out-%d" % (part.id, i) for i in range(spec.outputs)]
    part_ids = {neuron_id: part.id for neuron_id in inputs + outputs}

    for child in part.child:
        ci, co, cp = _extract_io(body_spec, child.part)
        inputs += ci
        outputs += co
        part_ids.update(cp)

    return inputs, outputs, part_ids


class NeuralNetworkGenerator(object):
    """
    Simple random neural network generator, generates
    hidden neurons and connections with a certain probability
    from a specified input / output interface.
    """
    def __init__(self, spec, max_hidden=20, conn_prob=0.1):
        """
        :param conn_prob: Probability of creating a weight between two neurons.
        :type conn_prob: float
        :param spec:
        :type spec: NeuralNetImplementation
        :param max_hidden:
        :return:
        """
        self.conn_prob = conn_prob
        self.spec = spec

        types = spec.get_all_types()
        self.layer_types = {
            layer: [t for t in types if layer in spec.get(t).layers]
            for layer in ("input", "output", "hidden")
        }

        self.max_hidden = max_hidden

    def generate(self, inputs, outputs, part_ids=None):
        """
        Generates a neural network from the provided interface.
        :param inputs: A list of IDs of all input neurons that should
               be generated.
        :type inputs: list
        :param outputs: List of output IDs to be generated
        :type outputs: list
        :param part_ids: Maps neuron ID to corresponding part ID
        :type part_ids: dict
        :return: The generated NeuralNetwork protobuf
        :rtype: NeuralNetwork
        """
        net = NeuralNetwork()
        hidden = []

        if part_ids is None:
            part_ids = {}

        # Initialize network interface, i.e. inputs and outputs
        for layer, ids in (("input", inputs), ("output", outputs)):
            for neuron_id in ids:
                neuron = net.neuron.add()
                neuron.id = neuron_id
                neuron.layer = layer

                if neuron_id in part_ids:
                    neuron.partId = part_ids[neuron_id]

                neuron.type = self.choose_neuron_type(layer)
                spec = self.spec.get(neuron.type)
                self.initialize_neuron(spec, neuron)

        num_hidden = self.choose_num_hidden()
        for i in range(num_hidden):
            neuron = net.neuron.add()
            neuron.id = 'brian-gen-hidden-%s' % len(hidden)
            hidden.append(neuron.id)
            neuron.layer = "hidden"
            neuron.type = self.choose_neuron_type(neuron.layer)
            spec = self.spec.get(neuron.type)
            self.initialize_neuron(spec, neuron)

        # Initialize neuron connections
        conn_start = inputs + hidden + outputs
        conn_end = hidden + outputs

        for src, dst in itertools.izip(conn_start, conn_end):
            weight = self.choose_weight(src, dst)

            if weight < EPSILON:
                continue

            conn = net.connection.add()
            conn.src = src
            conn.dst = dst
            conn.weight = weight

        return net

    def generate_from_body(self, body, body_spec):
        """
        Convenience wrapper over `generate` to fetch the network
        interface from a robot body.
        :param body:
        :type body: Body
        :param body_spec:
        :type body_spec: BodyImplementation
        :return: NeuralNetwork
        """
        inputs, outputs, part_ids = _extract_io(body_spec, body.root)
        return self.generate(inputs, outputs, part_ids)

    def choose_weight(self, src, dst):
        """
        Overridable function to pick a neural connection weight.
        By default, 0 is returned with probability 1 - `conn_prob` and
        a weight between 0 and 1 is returned with probability `conn_prob`.
        :param src:
        :param dst:
        :return:
        :rtype: float
        """
        return random.random() if random.random() <= self.conn_prob else 0

    def initialize_neuron(self, spec, neuron):
        """
        Initializes a neuron's parameters
        :param spec:
        :type spec: NeuronSpec
        :param neuron:
        :type neuron: Neuron
        :return:
        """
        # Initialize random parameters
        import sys
        for p in spec.get_random_parameters(serialize=True):
            new_param = neuron.param.add()
            new_param.value = p

    def choose_neuron_type(self, layer):
        """
        Overridable method to pick the neuron type of a new neuron.
        :param layer:
        :return:
        """
        return random.choice(self.layer_types[layer])

    def choose_num_hidden(self):
        """
        Overridable method to pick the number of hidden
        neurons.
        :return:
        """
        return random.randint(0, self.max_hidden)
