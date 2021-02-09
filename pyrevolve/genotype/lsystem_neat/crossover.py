from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding, Alphabet
from pyrevolve.genotype.lsystem_neat.lsystem_neat_genotype import LSystemCPGHyperNEATGenotype
from pyrevolve.genotype.neat_brain_genome.crossover import NEATCrossoverConf
from pyrevolve.genotype.neat_brain_genome.crossover import standard_crossover as NEATBrainCrossover
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import generate_child_genotype as PlasticodingCrossover

import random


class CrossoverConfig:
    def __init__(self,
                 crossover_prob):
        """
        Creates a Crossover object that sets the configuration for the crossover operator

        :param crossover_prob: crossover probability
        """
        self.crossover_prob = crossover_prob


def standard_crossover(parents, lsystem_conf, crossover_conf):
    """
    Creates an child (individual) through crossover with two parents

    :param parents: Parents type Individual
    :param lsystem_conf: LSystemCPGHyperNEATGenotypeConfig type with config for NEAT and Plasticoding
    :param crossover_conf: CrossoverConfig for lsystem crossover type
    :return: brain and body crossover (Only body right now)
    """
    assert len(parents) == 2

    parents_body_genotype = [p.representation._body_genome for p in parents]
    parents_brain_genotypes = [pair for pair in zip(parents[0].representation._brain_genomes, parents[1].representation._brain_genomes)]

    child_genotype = LSystemCPGHyperNEATGenotype()
    Neatconf = NEATCrossoverConf()

    new_body = PlasticodingCrossover(parents_body_genotype, lsystem_conf.plasticoding, crossover_conf)
    new_brain = []
    for g1, g2 in parents_brain_genotypes:
        new_brain.append(NEATBrainCrossover([g1, g2], Neatconf, crossover_conf, lsystem_conf))

    child_genotype._body_genome = new_body
    child_genotype._brain_genomes = new_brain

    return child_genotype


