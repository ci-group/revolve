from pyrevolve.genotype.hyperplasticoding.hyperplasticoding import HyperPlasticoding
import neat
import random
from ....custom_logging.logger import genotype_logger
import sys
import os


def standard_mutation(genotype, mutation_conf):
    """
    Mutates genotype 

    :param genotype: genotype to be mutated
    :param mutation_conf: configuration for mutation

    :return: modified genotype
    """
    local_dir = os.path.dirname(__file__) + '/../'
    body_config_path = os.path.join(local_dir, 'config-body-nonplastic')

    body_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              body_config_path)

    mutation_attempt = random.uniform(0.0, 1.0)
    if mutation_attempt > mutation_conf.mutation_prob:
        return genotype

    else:

        genotype.cppn_body.mutate(body_config.genome_config)

        return genotype
