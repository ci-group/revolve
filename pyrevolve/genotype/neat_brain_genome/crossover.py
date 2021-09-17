import random

from pyrevolve.genotype.neat_brain_genome import NeatBrainGenome


class NEATCrossoverConf:
    def __init__(self):
        self.mate_average = True
        self.interspecies_crossover = True
        self.speciation = True


def standard_crossover(parents, NeatCrossoverConf, crossover_conf, lsystem_conf):
    """
    Creates an child (genotype) through crossover with two parents

    :param parents: parents brain genome to be used for crossover
    :param NeatCrossoverConf: NEAT genotype configuration object
    :param crossover_conf: CrossoverConfig for lsystem
    :return: genotype result of the crossover
    """
    assert len(parents) == 2

    crossover_attempt = random.uniform(0.0, 1.0)
    if crossover_attempt > crossover_conf.crossover_prob:
         new_genotype = parents[0]._neat_genome
    else:
        mother = parents[0]._neat_genome
        father = parents[1]._neat_genome
        new_genotype = mother.Mate(father,
                                   NeatCrossoverConf.mate_average,
                                   NeatCrossoverConf.interspecies_crossover,
                                   lsystem_conf.neat.rng,
                                   lsystem_conf.neat.multineat_params
                                   )
    child_genome = NeatBrainGenome()
    child_genome._brain_type = parents[0]._brain_type
    child_genome._neat_genome = new_genotype
    return child_genome
