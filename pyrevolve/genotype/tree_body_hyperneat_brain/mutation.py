from __future__ import annotations

from ..direct_tree.direct_tree_genotype import DirectTreeGenotype, DirectTreeGenotypeConfig
from ..direct_tree.direct_tree_mutation import mutate as directtree_mutate
from ..neat_brain_genome.mutation import mutation_blended as neat_mutation_blended
from ..neat_brain_genome import NeatBrainGenomeConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable
    from . import DirectTreeCPGHyperNEATGenotype
    from ..neat_brain_genome import NeatBrainGenome


class DirectTreeNeatMutationConf:
    def __init__(self,
                 direct_tree_mutation_conf: DirectTreeGenotypeConfig,
                 neat_conf: NeatBrainGenomeConfig):
        self.direct_tree = direct_tree_mutation_conf
        self.neat = neat_conf


def composite_mutation(genotype: DirectTreeCPGHyperNEATGenotype,
                       body_mutation: Callable[[DirectTreeGenotype], DirectTreeGenotype],
                       brain_mutation: Callable[[NeatBrainGenome], NeatBrainGenome]) -> DirectTreeCPGHyperNEATGenotype:
    new_genome = genotype.clone()
    new_genome._body_genome = body_mutation(new_genome._body_genome)
    for i in range(len(new_genome._brain_genomes)):
        new_genome._brain_genomes[i] = brain_mutation(new_genome._brain_genomes[i])
    return new_genome


def standard_mutation(genotype: DirectTreeCPGHyperNEATGenotype,
                      mutation_conf: DirectTreeNeatMutationConf) -> DirectTreeCPGHyperNEATGenotype:
    return composite_mutation(
        genotype,
        lambda g: directtree_mutate(g, mutation_conf.direct_tree, in_place=False),
        lambda g: neat_mutation_blended(g, mutation_conf.neat),
    )
