from __future__ import absolute_import

from pyrevolve.generate import NeuralNetworkGenerator
from pyrevolve.spec import default_neural_net

from .. import constants


def get_brain_spec(conf):
    """
    Returns the brain specification corresponding to the
    given config.
    :param conf:
    :return:
    """
    return default_neural_net(conf.brain_mutation_epsilon)


def get_brain_generator(conf):
    """
    Returns a brain generator.

    :param conf:
    :return:
    """
    return NeuralNetworkGenerator(
        get_brain_spec(conf),
        max_hidden=constants.MAX_HIDDEN_NEURONS,
        conn_prob=conf.p_connect_neurons
    )
