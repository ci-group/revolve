import random
import unittest
from revolve.generate import NeuralNetworkGenerator
from revolve.spec import NeuralNetImplementation, NeuronSpec


brain_spec = NeuralNetImplementation(
    {
        "Simple": NeuronSpec(params=["bias"]),
        "Oscillator": NeuronSpec(
            params=["period", "phase_offset", "amplitude"]
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

        inputs = ['input-1', 'input-2']
        outputs = ['output-1', 'output-2', 'output-3']
        gen = NeuralNetworkGenerator(
            brain_spec,
            inputs=inputs,
            outputs=outputs,
            max_hidden=20,
            input_types=['Input'],
            output_types=['Oscillator', 'Simple']
        )

        brain = gen.generate()
        self.assertTrue(brain.IsInitialized(), "Incomplete brain (seed %d)." % seed)

        def get_neuron(neuron_id):
            return [neuron for neuron in brain.neuron if neuron.id == neuron_id]

        # All inputs should be present
        for neuron_id in inputs:
            neurons = get_neuron(neuron_id)
            self.assertTrue(len(neurons) == 1, "Neuron %s not present." % neuron_id)
            self.assertEquals("input", neurons[0].layer, "Neuron %s should have 'input' layer.")

        # All outputs should be present
        for neuron_id in outputs:
            neurons = get_neuron(neuron_id)
            self.assertTrue(len(neurons) == 1, "Neuron %s not present." % neuron_id)
            self.assertEquals("output", neurons[0].layer, "Neuron %s should have 'output' layer.")