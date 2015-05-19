"""
Random generator for the default neural network
"""
import random
import itertools
from ..spec.protobuf import NeuralNetwork, Neuron
from ..spec import NeuralNetImplementation, NeuronSpec


def _init_neuron_list(spec, neurons):
    specs = {neuron_type: spec.get(neuron_type) for neuron_type in neurons}
    none_values = [k for k in specs if specs[k] is None]
    if none_values:
        raise ValueError("Invalid neuron type(s): %s"
                         % ', '.join(none_values))

    return specs

# Epsilon value below which neuron weights are discarded
EPSILON = 1e-11


class NeuralNetworkGenerator(object):
    """
    Simple random neural network generator, generates
    hidden neurons and connections with a certain probability
    from a specified input / output interface.
    """
    def __init__(self, spec, inputs=None, outputs=None, max_hidden=20, input_types=None, output_types=None,
                 hidden_types=None, conn_prob=0.1):
        """
        :param conn_prob: Probability of creating a weight between two neurons.
        :type conn_prob: float
        :param input_types: Allowed types for input layer
        :type input_types: list
        :param output_types: Allowed types for output layer
        :type output_types: list
        :param hidden_types: Allowed types for hidden layer
        :type hidden_types: list
        :param spec:
        :type spec: NeuralNetImplementation
        :param inputs: A list of IDs of all input neurons that should
                       be generated.
        :type inputs: list
        :param outputs: List of output IDs to be generated
        :type outputs: list
        :param max_hidden:
        :return:
        """
        self.conn_prob = conn_prob
        self.spec = spec
        self.inputs = [] if inputs is None else inputs
        self.outputs = [] if outputs is None else outputs
        self.hidden = []
        self.input_types = ['Input'] if input_types is None else input_types
        self.output_types = [] if output_types is None else output_types
        self.hidden_types = self.output_types if hidden_types is None else hidden_types

        # Validate neuron types
        _init_neuron_list(spec, self.input_types)
        _init_neuron_list(spec, self.output_types)
        _init_neuron_list(spec, self.hidden_types)

        self.max_hidden = max_hidden

    def generate(self):
        """
        :return:
        :rtype: NeuralNetwork
        """
        net = NeuralNetwork()

        # Initialize neurons in all layers
        for layer, ids in (("input", self.inputs), ("output", self.outputs)):
            for neuron_id in ids:
                neuron = net.neuron.add()
                neuron.id = neuron_id
                neuron.layer = layer
                neuron.type = self.choose_neuron_type(layer)
                spec = self.spec.get(neuron.type)
                self.initialize_neuron(spec, neuron)

        num_hidden = self.choose_num_hidden()
        for i in range(num_hidden):
            neuron = net.neuron.add()
            neuron.id = 'brian-gen-hidden-%s' % len(self.hidden)
            self.hidden.append(neuron.id)
            neuron.layer = "hidden"
            neuron.type = self.choose_neuron_type(neuron.layer)
            spec = self.spec.get(neuron.type)
            self.initialize_neuron(spec, neuron)

        # Initialize neuron connections
        conn_start = self.inputs + self.hidden + self.outputs
        conn_end = self.hidden + self.outputs

        for src, dst in itertools.izip(conn_start, conn_end):
            weight = self.choose_weight(src, dst)

            if weight < EPSILON:
                continue

            conn = net.connection.add()
            conn.src = src
            conn.dst = dst
            conn.weight = weight

        return net

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
        for p in spec.get_random_parameters(serialize=True):
            new_param = neuron.param.add()
            new_param.value = p

    def choose_neuron_type(self, layer):
        """
        Overridable method to pick the neuron type of a new neuron.
        :param layer:
        :return:
        """
        if layer == "input":
           values = self.input_types
        elif layer == "output":
            values = self.output_types
        elif layer == "hidden":
            values = self.hidden_types
        else:
            raise ValueError("Unknown layer '%s'" % layer)

        return random.choice(values)

    def choose_num_hidden(self):
        """
        Overridable method to pick the number of hidden
        neurons.
        :return:
        """
        return random.randint(0, self.max_hidden)
