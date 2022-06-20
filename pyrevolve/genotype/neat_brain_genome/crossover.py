import random

from pyrevolve.genotype.neat_brain_genome import NeatBrainGenome


class NEATCrossoverConf:
    def __init__(self):
        self.mate_average = True
        self.interspecies_crossover = True
        self.speciation = True
        self.apply_constraints: bool = True


def standard_crossover(parents, neat_crossover_conf: NEATCrossoverConf, crossover_conf, lsystem_conf):
    """
    Creates an child (genotype) through crossover with two parents

    :param parents: parents brain genome to be used for crossover
    :param neat_crossover_conf: NEAT genotype configuration object
    :param crossover_conf: CrossoverConfig
    :return: genotype result of the crossover
    """
    assert len(parents) == 2

    crossover_attempt = random.uniform(0.0, 1.0)
    if crossover_attempt > crossover_conf.crossover_prob:
        new_genotype = parents[0]._neat_genome
    else:
        mother = parents[0]._neat_genome
        father = parents[1]._neat_genome
        if neat_crossover_conf.apply_constraints:
            new_genotype = mother.MateWithConstraints(father,
                                                      neat_crossover_conf.mate_average,
                                                      neat_crossover_conf.interspecies_crossover,
                                                      lsystem_conf.neat.rng,
                                                      lsystem_conf.neat.multineat_params
                                                      )
        else:
            new_genotype = mother.Mate(father,
                                       neat_crossover_conf.mate_average,
                                       neat_crossover_conf.interspecies_crossover,
                                       lsystem_conf.neat.rng,
                                       lsystem_conf.neat.multineat_params
                                       )
    child_genome = NeatBrainGenome()
    child_genome._brain_type = parents[0]._brain_type
    child_genome._neat_genome = new_genotype
    return child_genome
