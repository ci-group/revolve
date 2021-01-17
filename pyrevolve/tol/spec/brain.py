from __future__ import absolute_import

#from pyrevolve.generate import NeuralNetworkGenerator
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

