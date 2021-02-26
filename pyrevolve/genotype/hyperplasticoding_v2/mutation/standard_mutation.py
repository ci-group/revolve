from pyrevolve.genotype.hyperplasticoding_v2.hyperplasticoding import HyperPlasticoding
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

    cppn_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                              neat.DefaultSpeciesSet, neat.DefaultStagnation,
                              mutation_conf.cppn_config_path)

    # mutate cppn
    mutation_attempt = random.uniform(0.0, 1.0)
    if mutation_attempt <= mutation_conf.mutation_prob:
        genotype.cppn.mutate(cppn_config.genome_config)

    # TODO: mutate querying seed
    #mutation_attempt = 1#random.uniform(0.0, 1.0)
    #if mutation_attempt <= mutation_conf.mutation_prob:
        #print('parent seed',  genotype.querying_seed)
        #genotype.querying_seed+= blabla
        #print('child seed',  genotype.querying_seed)

    return genotype
