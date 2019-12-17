from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding, Alphabet, PlasticodingConfig
from pyrevolve.evolution.individual import Individual
import random
from ....custom_logging.logger import genotype_logger


def generate_child_genotype(parent_genotypes, genotype_conf, crossover_conf):
    """
    Generates a child (individual) by randomly mixing production rules from two parents

    :param parents: parents to be used for crossover

    :return: child genotype
    """
    grammar = {}
    crossover_attempt = random.uniform(0.0, 1.0)
    if crossover_attempt > crossover_conf.crossover_prob:
        grammar = parent_genotypes[0].grammar
    else:
        for letter in Alphabet.modules():
            parent = random.randint(0, 1)
            # gets the production rule for the respective letter
            grammar[letter[0]] = parent_genotypes[parent].grammar[letter[0]]

    genotype = Plasticoding(genotype_conf, 'tmp')
    genotype.grammar = grammar
    return genotype.clone()


def standard_crossover(environments, parent_individuals, genotype_conf, crossover_conf):
    """
    Creates an child (individual) through crossover with two parents

    :param parent_genotypes: genotypes of the parents to be used for crossover
    :return: genotype result of the crossover
    """
    first_environment = list(environments.keys())[-1]

    parent_genotypes = [p[first_environment].genotype for p in parent_individuals]
    new_genotype = generate_child_genotype(parent_genotypes, genotype_conf, crossover_conf)

    #TODO what if you have more than 2 parents? fix log
    genotype_logger.info(
        f'crossover: for genome {new_genotype.id} - p1: {parent_genotypes[0].id} p2: {parent_genotypes[1].id}.')
    return new_genotype
