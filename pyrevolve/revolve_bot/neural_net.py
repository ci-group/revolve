"""
Random generator for the default neural network
"""
from __future__ import absolute_import
from __future__ import print_function

import random
import itertools

from pyrevolve.spec import NeuralNetwork
from pyrevolve.spec import NeuralNetImplementation
from pyrevolve.spec import BodyImplementation

from pyrevolve.util import decide


# Helper function to extract the network interface from a body part and subtree
def _extract_io(body_spec, part):
    spec = body_spec.get(part.type)
    inputs = ["{}-in-{}".format(part.id, i) for i in range(spec.inputs)]
    outputs = ["{}-out-{}".format(part.id, i) for i in range(spec.outputs)]
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
        :param conn_prob: Probability of creating a connection (i.e. nonzero
                          weight) between two neurons.
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

    def generate(self, inputs, outputs, part_ids=None, num_hidden=None,):
        """
        Generates a neural network from the provided interface.

        Note that hidden neurons will get a randomly assigned part ID from
        the specified `part_ids` map, provided it isn't empty.

        :param inputs: A list of IDs of all input neurons that should
               be generated.
        :type inputs: list
        :param outputs: List of output IDs to be generated
        :type outputs: list
        :param part_ids: Maps neuron ID to corresponding part ID. This is
                         required to set the `partId` field on a neuron.
        :type part_ids: dict
        :param num_hidden: If specified, this number of hidden neurons will
                           be generated for the brain.
        :return: The generated NeuralNetwork protobuf
        :rtype: NeuralNetwork
        """
        net = NeuralNetwork()
        hidden = []

        if part_ids is None:
            part_ids = {}

        # Create a list of unique part IDs to choose hidden neuron
        # part IDs from.
        part_list = list(set(part_ids.values()))

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

        num_hidden = self.choose_num_hidden() if num_hidden is None \
            else num_hidden
        for i in range(num_hidden):
            neuron = net.neuron.add()
            neuron.id = 'brian-gen-hidden-{}'.format(len(hidden))

            # Assign a part ID to each hidden neuron, provided we
            # have a map.
            if part_list:
                neuron.partId = random.choice(part_list)

            hidden.append(neuron.id)
            neuron.layer = "hidden"
            neuron.type = self.choose_neuron_type(neuron.layer)
            spec = self.spec.get(neuron.type)
            self.initialize_neuron(spec, neuron)

        # Initialize neuron connections
        conn_start = inputs + hidden + outputs
        conn_end = hidden + outputs

        for src, dst in itertools.product(conn_start, conn_end):
            if not decide(self.conn_prob):
                continue

            weight = self.choose_weight()

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

    @staticmethod
    def choose_weight():
        """
        Overridable function to pick a neural connection weight.
        By default, this returns a value between 0 and 1
        :return:
        :rtype: float
        """
        return random.random()

    @staticmethod
    def initialize_neuron(spec, neuron):
        """
        Initializes a neuron's parameters
        :param spec:
        :type spec: NeuronSpec
        :param neuron:
        :type neuron: Neuron
        :return:
        """
        # Initialize random parameters
        spec.set_parameters(neuron.param, spec.get_random_parameters())

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
