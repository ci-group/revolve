#!/usr/bin/env python3

import unittest
import numpy as np
import multineat as NEAT


class RawGenomeTest(unittest.TestCase):

    @staticmethod
    def parameters():
        params = NEAT.Parameters()
        params.PopulationSize = 100
        params.DynamicCompatibility = True
        params.NormalizeGenomeSize = True
        params.WeightDiffCoeff = 0.1
        params.CompatTreshold = 2.0
        params.YoungAgeTreshold = 15
        params.SpeciesMaxStagnation = 15
        params.OldAgeTreshold = 35
        params.MinSpecies = 2
        params.MaxSpecies = 10
        params.RouletteWheelSelection = False
        params.RecurrentProb = 0.0
        params.OverallMutationRate = 1.0

        params.ArchiveEnforcement = False

        params.MutateWeightsProb = 0.05

        params.WeightMutationMaxPower = 0.5
        params.WeightReplacementMaxPower = 8.0
        params.MutateWeightsSevereProb = 0.0
        params.WeightMutationRate = 0.25
        params.WeightReplacementRate = 0.9

        params.MaxWeight = 8

        params.MutateAddNeuronProb = 0.001
        params.MutateAddLinkProb = 0.3
        params.MutateRemLinkProb = 0.0

        params.MinActivationA = 4.9
        params.MaxActivationA = 4.9

        params.ActivationFunction_SignedSigmoid_Prob = 0.0
        params.ActivationFunction_UnsignedSigmoid_Prob = 1.0
        params.ActivationFunction_Tanh_Prob = 0.0
        params.ActivationFunction_SignedStep_Prob = 0.0

        params.CrossoverRate = 0.0
        params.MultipointCrossoverRate = 0.0
        params.SurvivalRate = 0.2

        params.MutateNeuronTraitsProb = 0
        params.MutateLinkTraitsProb = 0

        params.AllowLoops = True
        params.AllowClones = True

        params.ClearNeuronTraitParameters()
        params.ClearLinkTraitParameters()
        params.ClearGenomeTraitParameters()

        return params

    def activate_network(self, genome, _input=None):
        genome.BuildPhenotype(self._net)
        _input = np.array([1, 2, 3], dtype=float) if _input is None else _input
        self._net.Input(_input)
        self._net.Activate()
        output = self._net.Output()
        return output[0]

    def setUp(self):
        self._params = self.parameters()
        self._net = NEAT.NeuralNetwork()
        self._rng = NEAT.RNG()
        self._rng.Seed(0)
        self._innov_db = NEAT.InnovationDatabase()

    def test_genome(self):
        a = NEAT.Genome(1, 3, 0, 1, False, NEAT.ActivationFunction.UNSIGNED_SIGMOID,
                   NEAT.ActivationFunction.UNSIGNED_SIGMOID, 0, self._params, 0)
        # a.PrintAllTraits()
        self.assertEqual(a.GetID(), 1)
        self.assertIsNotNone(self.activate_network(a))

        a.SetID(2)
        self.assertEqual(a.GetID(), 2)

    def test_genome_mutate(self):
        a = NEAT.Genome(1, 3, 0, 1, False, NEAT.ActivationFunction.UNSIGNED_SIGMOID,
                        NEAT.ActivationFunction.UNSIGNED_SIGMOID, 0, self._params, 0)
        self._innov_db.Init_with_genome(a)
        output_1 = self.activate_network(a)
        for i in range(10):
            a.Mutate(False, NEAT.SearchMode.COMPLEXIFYING, self._innov_db, self._params, self._rng)
        output_2 = self.activate_network(a)
        # a.PrintAllTraits()
        self.assertEqual(a.GetID(), 1)
        self.assertIsNotNone(output_1)
        self.assertNotAlmostEqual(output_1, output_2)

    def test_genome_clone(self):
        a = NEAT.Genome(1, 3, 0, 1, False, NEAT.ActivationFunction.UNSIGNED_SIGMOID,
                        NEAT.ActivationFunction.UNSIGNED_SIGMOID, 0, self._params, 0)
        self._innov_db.Init_with_genome(a)
        a.Mutate(False, NEAT.SearchMode.COMPLEXIFYING, self._innov_db, self._params, self._rng)
        b = NEAT.Genome(a)
        self.assertEqual(a.NumNeurons(), b.NumNeurons())
        self.assertEqual(a.NumLinks(), b.NumLinks())
        self.assertEqual(a.NumInputs(), b.NumInputs())
        self.assertEqual(a.NumOutputs(), b.NumOutputs())

        self.assertAlmostEqual(self.activate_network(a), self.activate_network(b))

    def test_genome_crossover(self):
        a = NEAT.Genome(1, 3, 0, 1, False, NEAT.ActivationFunction.UNSIGNED_SIGMOID,
                        NEAT.ActivationFunction.UNSIGNED_SIGMOID, 0, self._params, 0)
        self._innov_db.Init_with_genome(a)
        a.Mutate(False, NEAT.SearchMode.COMPLEXIFYING, self._innov_db, self._params, self._rng)
        b = NEAT.Genome(a)
        b.SetID(2)
        for i in range(10):
            b.Mutate(False, NEAT.SearchMode.COMPLEXIFYING, self._innov_db, self._params, self._rng)
        # b.PrintAllTraits()

        c = a.Mate(b, True, True, self._rng, self._params)
        c.SetID(3)
        self.assertEqual(c.GetID(), 3)
        output_a = self.activate_network(a)
        output_b = self.activate_network(b)
        output_c = self.activate_network(c)
        self.assertIsNotNone(output_c)
        self.assertNotAlmostEqual(output_a, output_c)
        self.assertNotAlmostEqual(output_b, output_c)

        for i in range(10):
            c.Mutate(False, NEAT.SearchMode.COMPLEXIFYING, self._innov_db, self._params, self._rng)
        output_c = self.activate_network(c)
        self.assertIsNotNone(output_c)
        self.assertNotAlmostEqual(output_a, output_c)
        self.assertNotAlmostEqual(output_b, output_c)
        # c.PrintAllTraits()


if __name__ == "__main__":
    unittest.main()
