#!/usr/bin/env python3

import unittest


class ImportTest(unittest.TestCase):
    def test_import(self):
        import multineat
        # enums
        self.assertIsNotNone(multineat.NeuronType)
        self.assertIsNotNone(multineat.ActivationFunction)
        self.assertIsNotNone(multineat.SearchMode)

        # random generator
        self.assertIsNotNone(multineat.RNG)

        # nn
        self.assertIsNotNone(multineat.Connection)
        self.assertIsNotNone(multineat.Neuron)
        self.assertIsNotNone(multineat.NeuralNetwork)
        self.assertIsNotNone(multineat.NeuralNetwork)

        # gene
        self.assertIsNotNone(multineat.LinkGene)
        self.assertIsNotNone(multineat.NeuronGene)
        self.assertIsNotNone(multineat.Genome)

        self.assertIsNotNone(multineat.Species)

        self.assertIsNotNone(multineat.Substrate)

        self.assertIsNotNone(multineat.PhenotypeBehavior)

        self.assertIsNotNone(multineat.Population)
        self.assertIsNotNone(multineat.Innovation)
        self.assertIsNotNone(multineat.InnovationDatabase)

        self.assertIsNotNone(multineat.Parameters)

        self.assertIsNotNone(multineat.DoublesList)
        self.assertIsNotNone(multineat.DoublesList2D)
        self.assertIsNotNone(multineat.FloatsList)
        self.assertIsNotNone(multineat.FloatsList2D)
        self.assertIsNotNone(multineat.IntsList)
        self.assertIsNotNone(multineat.IntsList2D)
        self.assertIsNotNone(multineat.GenomeList)
        self.assertIsNotNone(multineat.NeuronList)
        self.assertIsNotNone(multineat.ConnectionList)
        self.assertIsNotNone(multineat.NeuronGeneList)
        self.assertIsNotNone(multineat.LinkGeneList)
        self.assertIsNotNone(multineat.PhenotypeBehaviorList)


if __name__ == "__main__":
    unittest.main()
