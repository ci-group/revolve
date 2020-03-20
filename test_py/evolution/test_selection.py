
from __future__ import absolute_import

import unittest

from pyrevolve.evolution.selection import multiple_selection, tournament_selection

from .tools import get_population, get_population_speciated

class TestSelection(unittest.TestCase):
    """
    Tests the Selection class
    """
    def test_population(self):
        population = get_population(random_fitness=True)

        # TODO how to test random tournament selection

        # TODO how to test multiple selection

    def test_multiple_selection(self):
        population = get_population_speciated(random_fitness=True)

        # TODO how to test random tournament selection

        # TODO how to test multiple selection







