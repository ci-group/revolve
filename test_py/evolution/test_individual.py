from __future__ import absolute_import

import unittest

from pyrevolve.evolution.individual import Individual

from pyrevolve.genotype.lsystem_neat.lsystem_neat_genotype import LSystemCPGHyperNEATGenotype

from .tools import get_genotype

class TestIndividual(unittest.TestCase):
    """
    Tests the individual class
    """
    genotype = get_genotype()

    def test_genotype(self):

        individual = Individual(genotype=self.genotype)

        self.assertEqual(individual.phenotype, None)

        individual.develop()

        self.assertEqual(individual.genotype, self.genotype)
        self.assertNotEqual(individual.phenotype, None)


    def test_phenotype(self):

        phenotype = self.genotype.develop()

        individual = Individual(genotype=phenotype, phenotype=phenotype)

        self.assertEqual(individual.genotype, self.genotype)
        self.assertEqual(individual.phenotype, phenotype)

    def test_export(self):
        # TODO test exporting the genotype, phenotype and fitness.
        pass

