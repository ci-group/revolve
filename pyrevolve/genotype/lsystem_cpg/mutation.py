from .cpg_brain import CPGBrainGenomeConfig, CPGBrainGenome
from ..plasticoding.mutation.standard_mutation import standard_mutation as plasticondig_mutation

from ..plasticoding.mutation.mutation import MutationConfig as PlasticodingMutationConf, MutationConfig


class LSystemCPGMutationConf:
    def __init__(self,
                 plasticoding_mutation_conf: PlasticodingMutationConf,
                 cpg_conf: CPGBrainGenomeConfig):
        self.plasticoding = plasticoding_mutation_conf
        self.cpg = cpg_conf


def composite_mutation(genotype, body_mutation):
    new_genome = genotype.clone()
    new_genome._body_genome = body_mutation(new_genome._body_genome)
    new_genome._brain_genome = CPGBrainGenome()
    return new_genome


def standard_mutation(genotype, mutation_conf: MutationConfig):
    return composite_mutation(
        genotype,
        lambda g: plasticondig_mutation(g, mutation_conf)
    )
