from pyrevolve.genotype.hyperplasticoding.hyperplasticoding import HyperPlasticoding, HyperPlasticodingConfig
import neat
from pyrevolve.evolution.individual import Individual
import random
import os
from ....custom_logging.logger import genotype_logger


def standard_crossover(environments, parent_individuals, genotype_conf, crossover_conf):
    """
    Creates an child (individual) through crossover with two parents

    :param parent_genotypes: genotypes of the parents to be used for crossover
    :return: genotype result of the crossover
    """

    local_dir = os.path.dirname(__file__)+'/../'

    body_config_path = os.path.join(local_dir, 'config-body-nonplastic')
    body_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                   neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                   body_config_path)
    brain_config_path = os.path.join(local_dir, 'config-brain-nonplastic')
    brain_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                               neat.DefaultSpeciesSet, neat.DefaultStagnation,
                               brain_config_path)

    first_environment = list(environments.keys())[-1]

    new_genotype = HyperPlasticoding(genotype_conf, 'tmp')

    parent_genotypes = [p[first_environment].genotype for p in parent_individuals]
    parent1_body = parent_genotypes[0].cppn_body
    parent2_body = parent_genotypes[1].cppn_body
    parent1_brain = parent_genotypes[0].cppn_brain
    parent2_brain = parent_genotypes[1].cppn_brain

    print('\n\n\ndskjnfsjnds', parent_genotypes[0].id, parent1_body.fitness, parent_genotypes[1].id, parent2_body.fitness)


    crossover_attempt = random.uniform(0.0, 1.0)
    if crossover_attempt > crossover_conf.crossover_prob:
        #TODO: replace this for simply deeply copying one random parent (not sure if would work as expected)
        new_body_cppn = body_config.genome_type(0)
        new_body_cppn.configure_crossover(parent1_body, parent1_body, body_config.genome_config)
        new_brain_cppn = brain_config.genome_type(0)
        new_brain_cppn.configure_crossover(parent1_brain, parent1_brain, brain_config.genome_config)
    else:
        new_body_cppn = body_config.genome_type(0)
        new_body_cppn.configure_crossover(parent1_body, parent2_body, body_config.genome_config)
        new_brain_cppn = brain_config.genome_type(0)
        new_brain_cppn.configure_crossover(parent1_brain, parent2_brain, brain_config.genome_config)

    new_genotype.cppn_body = new_body_cppn
    new_genotype.cppn_brain = new_brain_cppn

    genotype_logger.info(
        f'crossover: for genome {new_genotype.id} - p1: {parent_genotypes[0].id} p2: {parent_genotypes[1].id}.')
    return new_genotype
