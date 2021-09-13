from .genotype import Genotype
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig as Config
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding import Plasticoding
def mutate(genotype: Genotype, config: Config) -> Genotype:
    #return genotype # TODO!
    gen = Plasticoding(config.genotype_conf)
    gen.grammar = genotype.genotype_impl

    mutatedgenotype = standard_mutation(gen, config)

    genotype.genotype_impl = mutatedgenotype.grammar

    return genotype