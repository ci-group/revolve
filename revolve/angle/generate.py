"""
Generates a robot tree with the help of Revolve.Generate. This is a bit
backwards, but it allows for more configurability. A generator is defined
with a body generator and a neural net generator. First, a body is
generated. The interface of this body is then fed to the neural net
generator resulting in a neural network.
"""
import random
from ..generate import NeuralNetworkGenerator, BodyGenerator
from .representation import Tree, Node


def _get_node_list(body_part):
    """
    Returns a list of all node IDs starting
    at the given body part.
    :param body_part: BodyPart
    :return:
    """
    ids = [body_part.id]
    for conn in body_part.child:
        ids += _get_node_list(conn.part)

    return ids


class TreeGenerator(object):
    def __init__(self, body_gen, brain_gen):
        """
        :param body_gen:
        :type body_gen: BodyGenerator
        :param brain_gen: Neural network generator. Note that this generator
                          should set the partId property of input / output
                          neurons.
        :type brain_gen: NeuralNetworkGenerator
        :return:
        """
        self.body_gen = body_gen
        self.brain_gen = brain_gen

    def generate_tree(self):
        """
        Generates a new robot tree

        :return:
        :rtype: Tree
        """
        # Generate a body
        body = self.body_gen.generate()

        # Generate a brain from this body
        brain = self.brain_gen.generate_from_body(body, self.body_gen.spec)

        # Distribute the hidden neurons in the tree
        # randomly over the tree nodes.
        ids = _get_node_list(body.root)
        neuron_map = {}
        for neuron in brain.neuron:
            if neuron.layer == "hidden" and not neuron.HasField("partId"):
                neuron.partId = random.choice(ids)

            if not neuron.HasField("partId"):
                raise Exception("Neuron %s not associated with part." % neuron.id)

            neuron_map[neuron.id] = neuron

        # Create the tree without neural net connections
        root = self._create_subtree(body.root, brain)
        tree = Tree(root)

        # Create the neural net connections. We only
        # have the id <-> id paths, so we'll have to
        # locate the neurons in the tree and then
        # build the paths.
        for conn in brain.connection:
            src_neuron = neuron_map[conn.src]
            dst_neuron = neuron_map[conn.dst]
            src_node = tree.get_node(src_neuron.partId)
            dst_node = tree.get_node(dst_neuron.partId)
            src_node.add_neural_connection(src_neuron, dst_neuron, dst_node, conn.weight)

        return tree

    def _create_subtree(self, body_part, brain):
        """
        :param body_part:
        :param brain:
        :return:
        """
        # Gather neurons for this part
        neurons = [neuron for neuron in brain.neuron if neuron.partId == body_part.id]
        node = Node(body_part, neurons, self.body_gen.spec)
        for conn in body_part.child:
            subtree = self._create_subtree(conn.part, brain)
            node.add_connection(conn.src, conn.dst, subtree)

        return node


