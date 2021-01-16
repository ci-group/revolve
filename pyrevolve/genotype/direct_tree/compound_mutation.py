from typing import Callable

from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenome
from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeNEATGenotype
from pyrevolve.genotype.direct_tree.tree_mutation import DirectTreeMutationConfig
from pyrevolve.genotype.neat_brain_genome import NeatBrainGenomeConfig, NeatBrainGenome


class DirectTreeNEATMutationConfig:
    def __init__(self,
                 tree_mutation_conf: DirectTreeMutationConfig,
                 neat_conf: NeatBrainGenomeConfig):
        self.tree_mutation = tree_mutation_conf
        self.neat = neat_conf


def composite_mutation(genotype: DirectTreeNEATGenotype,
                       body_mutation: Callable[[DirectTreeGenome], DirectTreeGenome],
                       brain_mutation: Callable[[NeatBrainGenome], NeatBrainGenome]) -> DirectTreeNEATGenotype:
    new_genome = genotype.clone()
    new_genome._body_genome = body_mutation(new_genome._body_genome)
    for i in range(len(new_genome._brain_genomes)):
        new_genome._brain_genomes[i] = brain_mutation(new_genome._brain_genomes[i])
    return new_genome


def standard_mutation(genotype: DirectTreeNEATGenotype,
                      mutation_conf: DirectTreeNEATMutationConfig) -> DirectTreeNEATGenotype:
    return composite_mutation(
        genotype,
        lambda g: direct_tree_mutation(g, mutation_conf.tree_mutation),
        lambda g: neat_mutation(g, mutation_conf.neat),
    )