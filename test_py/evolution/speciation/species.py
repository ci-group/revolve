import os
import shutil
import unittest

import yaml

from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.speciation.species import Species
from pyrevolve.genotype import Genotype


class FakeGenome(Genotype):
    def __init__(self, _id: int):
        self.id = _id


class SpeciesTest(unittest.TestCase):
    TEST_FOLDER = '/tmp/species_test'

    def _create_clean_test_folder(self):
        if os.path.exists(self.TEST_FOLDER):
            shutil.rmtree(self.TEST_FOLDER)
        os.mkdir(self.TEST_FOLDER)

    def _generate_individuals(self):
        return [Individual(FakeGenome(i)) for i in range(20)]

    def _generate_species(self, _id: int = 42, individuals=None):
        if individuals is None:
            individuals = self._generate_individuals()
        return Species(individuals, _id)

    def test_instancing(self):
        s = self._generate_species()
        self.assertIsInstance(s, Species)

    def test_serialize(self):
        s = self._generate_species(33)
        self._create_clean_test_folder()
        species_file = os.path.join(self.TEST_FOLDER, 'species_33.yaml')
        s.serialize(species_file)

        self.assertTrue(os.path.isfile(species_file))
        with open(species_file) as file:
            data = yaml.load(file, Loader=yaml.SafeLoader)

        self.assertDictEqual(data, {
            'id': 33,
            'age': {'evaluations': 0, 'generations': 0, 'no_improvements': 0},
            'individuals_ids': [i for i in range(20)]
        })

    def test_deserialize(self):
        individuals = self._generate_individuals()
        s = self._generate_species(33, individuals)
        self._create_clean_test_folder()
        species_file = os.path.join(self.TEST_FOLDER, 'species_33.yaml')
        s.serialize(species_file)

        loaded_individuals = {
            individual.id: individual for individual in individuals
        }
        s1 = Species.Deserialize(species_file, loaded_individuals)

        self.assertEqual(s._id, s1._id)
        self.assertEqual(s.age.evaluations(), s1.age.evaluations())
        self.assertEqual(s.age.generations(), s1.age.generations())
        self.assertEqual(s.age.no_improvements(), s1.age.no_improvements())
        for (individual1, fit1), (individual2, fit2) in zip(s._individuals, s1._individuals):
            self.assertEqual(individual1, individual2)
            self.assertEqual(fit1, fit2)

        # test also the equality operators
        self.assertEqual(s.age, s1.age)
        self.assertEqual(s, s1)
