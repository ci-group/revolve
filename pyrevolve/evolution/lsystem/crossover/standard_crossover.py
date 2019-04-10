from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding, Alphabet, PlasticodingConfig
from pyrevolve.evolution.individual import Individual
import random
import os
import logging

crossover_logger = logging.getLogger('__name__')
crossover_logger.setLevel(logging.INFO)

fh = logging.FileHandler('mut-cross.log', mode='w')
fh.setLevel(logging.INFO)

formatter = logging.Formatter('%(message)s')
fh.setFormatter(formatter)
crossover_logger.addHandler(fh)

def generate_child_genotype(parents):
	"""
	Generates a child (individual) by randomly mixing production rules from two parents

	:param parents: parents to be used for crossover

	:return: child genotype
	"""
	grammar = {}
	for letter in Alphabet.modules():
		parent = random.randint(0,1)
		# gets the production rule for the respective letter
		grammar[letter[0]] = parents[0].genotype.grammar[letter[0]]

	genotype = Plasticoding(PlasticodingConfig())
	genotype.grammar = grammar
	return genotype.clone()

def standard_crossover(parents):
	"""
	Creates an child (individual) through crossover with two parents

	:param parents: parents to be used for crossover

	:return: child (individual)
	"""
	genotype = generate_child_genotype(parents)
	child = Individual(genotype)
	crossover_logger.info(f'crossover: for genome {child.genotype.id} - p1: {parents[0].genotype.id} p2: {parents[1].genotype.id}.')
	return child

	