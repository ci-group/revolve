"""
Generates a robot tree with the help of Revolve.Generate. This is a bit
backwards, but it allows for more configurability. A generator is defined
with a body generator and a neural net generator. First, a body is
generated. The interface of this body is then fed to the neural net
generator resulting in a neural network.
"""
from ..generate import NeuralNetworkGenerator, BodyGenerator
from .representation import Tree


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

        return Tree.from_body_brain(body, brain, self.body_gen.spec)


