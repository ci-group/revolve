from typing import List

from pyrevolve.evolution.individual import Individual
from pyrevolve.genotype.direct_tree.direct_tree_crossover import crossover_list as direct_tree_crossover
from pyrevolve.genotype.neat_brain_genome.crossover import NEATCrossoverConf
from pyrevolve.genotype.neat_brain_genome.crossover import standard_crossover as NEATBrainCrossover
from pyrevolve.genotype.tree_body_hyperneat_brain import DirectTreeCPGHyperNEATGenotype, \
    DirectTreeCPGHyperNEATGenotypeConfig


class CrossoverConfig:
    def __init__(self, crossover_prob: float):
        """
        Creates a Crossover object that sets the configuration for the crossover operator

        :param crossover_prob: crossover probability
        """
        self.crossover_prob = crossover_prob


def standard_crossover(parents: List[Individual],
                       direct_tree_cpg_hyperneat_conf: DirectTreeCPGHyperNEATGenotypeConfig):
    """
    Creates an child (individual) through crossover with two parents

    :param parents: Parents type Individual
    :param direct_tree_cpg_hyperneat_conf: DirectTreeCPGHyperNEATGenotypeConfig type with config for DirectTree and NEAT
    :return: brain and body crossover (Only body right now)
    """
    assert len(parents) == 2

    parents_body_genotype = [p.genotype._body_genome for p in parents]
    parents_brain_genotypes = [pair for pair in
                               zip(parents[0].genotype._brain_genomes, parents[1].genotype._brain_genomes)]

    child_genotype = DirectTreeCPGHyperNEATGenotype()

    new_body = direct_tree_crossover(parents_body_genotype, direct_tree_cpg_hyperneat_conf.direct_tree)
    new_brain = []
    crossover_conf = CrossoverConfig(1.0)
    for g1, g2 in parents_brain_genotypes:
        new_brain.append(NEATBrainCrossover([g1, g2], direct_tree_cpg_hyperneat_conf.neat, crossover_conf, direct_tree_cpg_hyperneat_conf))

    child_genotype._body_genome = new_body
    child_genotype._brain_genomes = new_brain

    return child_genotype
