from typing import List

from ..plasticoding.crossover.standard_crossover import standard_crossover
from ..lsystem_body.genotype import Genotype
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig as Config
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding import Plasticoding

def crossover(parents: List[Genotype], config: Config) -> Genotype:
    pars = Plasticize(parents,config.genotype_conf)
    out = Deplasticize(standard_crossover({'plane':0.03},pars,config),config)
    return out

def Plasticize(parents,config):
    p = []
    for parent in (parents):
        gen = Plasticoding(config.plasticoding_config)
        gen.grammar = parent.genotype_impl
        p.append(gen)
    return p

def Deplasticize(genotype,config):
    gen = Genotype(genotype_impl=genotype.grammar)
    return gen
