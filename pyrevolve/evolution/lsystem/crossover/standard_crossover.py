from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding, Alphabet, PlasticodingConfig
from pyrevolve.evolution.individual import Individual
import random

def generate_child_genotype(parents):
	grammar = {}
	for letter in Alphabet.modules():
		parent = random.randint(0,1)
		# print(parents[0].genotype.grammar[letter[0]]) # gets the production rule for the respective letter
		grammar[letter[0]] = parents[0].genotype.grammar[letter[0]]

	genotype = Plasticoding(PlasticodingConfig)
	genotype.grammar = grammar
	return genotype

def standard_crossover(parents): # Parents = list of individual
	genotype = generate_child_genotype(parents)
	child = Individual(genotype)
	return child


	