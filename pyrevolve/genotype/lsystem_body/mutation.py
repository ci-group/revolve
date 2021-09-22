from pyrevolve.genotype.plasticoding import Plasticoding
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation

from .config import Config
from .genotype import Genotype


def mutate(genotype: Genotype, config: Config) -> Genotype:
    gen = Plasticoding(config.plasticoding_config,robot_id=0)
    gen.grammar = genotype.genotype_impl

    mutation_config = MutationConfig(config.mutation_prob, config.plasticoding_config)
    mutatedgenotype = standard_mutation(gen, mutation_config)

    copy = genotype.clone()
    copy.genotype_impl = mutatedgenotype.grammar

    return copy
