from __future__ import annotations

from ..plasticoding.mutation.standard_mutation import standard_mutation as plasticondig_mutation
from ..neat_brain_genome.mutation import mutation_complexify as neat_mutation
from ..plasticoding.mutation.mutation import MutationConfig as PlasticodingMutationConf
from ..neat_brain_genome import NeatBrainGenomeConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable
    from ..plasticoding import Plasticoding
    from . import LSystemCPGHyperNEATGenotype
    from ..neat_brain_genome import NeatBrainGenome


class LSystemNeatMutationConf:
    def __init__(self,
                 plasticoding_mutation_conf: PlasticodingMutationConf,
                 neat_conf: NeatBrainGenomeConfig):
        self.plasticoding = plasticoding_mutation_conf
        self.neat = neat_conf


def composite_mutation(genotype: LSystemCPGHyperNEATGenotype,
                       body_mutation: Callable[[Plasticoding], Plasticoding],
                       brain_mutation: Callable[[NeatBrainGenome], NeatBrainGenome]) -> LSystemCPGHyperNEATGenotype:
    new_genome = genotype.clone()
    new_genome._body_genome = body_mutation(new_genome._body_genome)
    new_genome._brain_genome = brain_mutation(new_genome._brain_genome)
    return new_genome


def standard_mutation(genotype: LSystemCPGHyperNEATGenotype,
                      mutation_conf: LSystemNeatMutationConf) -> LSystemCPGHyperNEATGenotype:
    return composite_mutation(
        genotype,
        lambda g: plasticondig_mutation(g, mutation_conf.plasticoding),
        lambda g: neat_mutation(g, mutation_conf.neat),
    )
