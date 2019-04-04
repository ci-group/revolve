from __future__ import absolute_import

import random
import unittest

from pyrevolve.generate import NeuralNetworkGenerator
from pyrevolve.spec import NeuralNetImplementation, NeuronSpec


brain_spec = NeuralNetImplementation(
    {
        "Simple": NeuronSpec(params=["bias"], layers=["hidden"]),
        "Oscillator": NeuronSpec(
            params=["period", "phase_offset", "amplitude"],
            layers=["hidden", "output"]
        )
    }
)


class TestNeuralNetGenerator(unittest.TestCase):
    """
    Some simple tests for generating a neural network
    """

    def test_valid(self):
        """
        Tests a valid neural network is generated
        :return:
        """
        seed = random.randint(0, 10000)
        random.seed(seed)

        gen = NeuralNetworkGenerator(
            brain_spec,
            max_hidden=20
        )

        inputs = ['input-1', 'input-2']
        outputs = ['output-1', 'output-2', 'output-3']
        brain = gen.generate(inputs=inputs, outputs=outputs)
        self.assertTrue(
                brain.IsInitialized(),
                "Incomplete brain (seed {seed}).".format(seed=seed))

        def get_neuron(neuron_id):
            return [neuron for neuron in brain.neuron if neuron.id == neuron_id]

        # All inputs should be present
        for neuron_id in inputs:
            neurons = get_neuron(neuron_id)
            self.assertTrue(
                    len(neurons) == 1,
                    "Neuron {n_id} not present.".format(n_id=neuron_id))
            self.assertEqual(
                    "input", neurons[0].layer,
                    "Neuron {n_id} should have 'input' (seed {seed}).".format(
                            n_id=neuron_id,
                            seed=seed
                    ))

        # All outputs should be present and have type oscillator
        for neuron_id in outputs:
            neurons = get_neuron(neuron_id)
            self.assertTrue(
                    len(neurons) == 1,
                    "Neuron {n_id} not present.".format(n_id=neuron_id))
            self.assertEqual(
                    "output", neurons[0].layer,
                    "Neuron {n_id} should have 'output' (seed {seed}).".format(
                            n_id=neuron_id,
                            seed=seed
                    ))
            self.assertEqual(
                    "Oscillator", neurons[0].type,
                    "Output neuron {n_id} should all be oscillators (seed "
                    "{seed}).".format(
                            n_id=neuron_id,
                            seed=seed
                    ))
