from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding, Alphabet, PlasticodingConfig
from pyrevolve.evolution.individual import Individual
import random
from ....custom_logging.logger import genotype_logger


def generate_child_genotype(parents, genotype_conf, crossover_conf, next_robot_id):
    """
    Generates a child (individual) by randomly mixing production rules from two parents

    :param parents: parents to be used for crossover

    :return: child genotype
    """
    grammar = {}
    crossover_attempt = random.uniform(0.0, 1.0)
    if crossover_attempt > crossover_conf.crossover_prob:
        grammar = parents[0].genotype.grammar
    else:
        for letter in Alphabet.modules():
            parent = random.randint(0, 1)
            # gets the production rule for the respective letter
            grammar[letter[0]] = parents[parent].genotype.grammar[letter[0]]

    genotype = Plasticoding(genotype_conf, next_robot_id)
    genotype.grammar = grammar
    return genotype.clone()


def standard_crossover(parents, genotype_conf, crossover_conf, next_robot_id):
    """
    Creates an child (individual) through crossover with two parents

    :param parents: parents to be used for crossover

    :return: child (individual)
    """
    genotype = generate_child_genotype(parents, genotype_conf, crossover_conf, next_robot_id)
    child = Individual(genotype)
    genotype_logger.info(
        f'crossover: for genome {child.genotype.id} - p1: {parents[0].genotype.id} p2: {parents[1].genotype.id}.')
    return child
