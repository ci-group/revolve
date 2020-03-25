from __future__ import absolute_import

import asyncio
import unittest

from pyrevolve.evolution.speciation.population_speciated import Speciation

from .helper import get_population_speciated


class TestPopulationSpeciated(unittest.TestCase):
    """
    Tests the population speciated class
    """

    def test_generation(self):
        population: Speciation = get_population_speciated()

        # TODO await?
        population.initialize()

        population.next_generation(1)

        # TODO test

    def test_recovered_individuals(self):
        # TODO
        pass

