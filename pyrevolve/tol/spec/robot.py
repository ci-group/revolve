from __future__ import absolute_import

from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from ..spec.body import get_body_generator
from ...revolve_bot.neural_net import NeuralNetworkGenerator
from ...spec import NeuralNetImplementation, NeuronSpec


def get_tree_generator(conf):
    """
    :param conf:
    :return:
    :rtype: TreeGenerator
    """
    body_gen = get_body_generator(conf)
    brain_spec = NeuralNetImplementation(
        {
            "Simple": NeuronSpec(params=["bias"]),
            "Oscillator": NeuronSpec(
                params=["period", "phaseOffset", "amplitude"]
            )
        }
    )
    brain_gen = NeuralNetworkGenerator(brain_spec)
    return RobogenTreeGenerator(body_gen, brain_gen, conf)
