from __future__ import absolute_import

import asyncio
import unittest

from pyrevolve.evolution.population.population import Population

from .helper import get_population


class TestPopulation(unittest.TestCase):
    """
    Tests the population class
    """

    def test_generation(self):
        population: Population = get_population()

        # TODO await?
        population.initialize()

        population.next_generation(1)

        # TODO test

    def test_recovered_individuals(self):
        # TODO
        pass

