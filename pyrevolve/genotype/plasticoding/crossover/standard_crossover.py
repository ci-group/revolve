from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding, Alphabet, PlasticodingConfig
from pyrevolve.evolution.individual import Individual
import random
from ....custom_logging.logger import genotype_logger


def generate_child_genotype(parents, crossover_conf):
    """
    Generates a child (individual) by randomly mixing production rules from two parents

    :param parents: parents to be used for crossover

    :return: child genotype
    """
    grammar = {}
    chance_of_crossover = random.uniform(0.0, 1.0)
    if chance_of_crossover <= crossover_conf.crossover_prob:
        grammar = parents[0].genotype.grammar
    else:
        for letter in Alphabet.modules():
            parent = random.randint(0, 1)
            # gets the production rule for the respective letter
            grammar[letter[0]] = parents[parent].genotype.grammar[letter[0]]

    genotype = Plasticoding(PlasticodingConfig())
    genotype.grammar = grammar
    return genotype.clone()


def standard_crossover(parents, crossover_conf):
    """
    Creates an child (individual) through crossover with two parents

    :param parents: parents to be used for crossover

    :return: child (individual)
    """
    genotype = generate_child_genotype(parents, crossover_conf)
    child = Individual(genotype)
    genotype_logger.info(
        f'crossover: for genome {child.genotype.id} - p1: {parents[0].genotype.id} p2: {parents[1].genotype.id}.')
    return child
