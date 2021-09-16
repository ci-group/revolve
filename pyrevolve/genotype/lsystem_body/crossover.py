from typing import List

from pyrevolve.genotype.plasticoding import Plasticoding

from ..lsystem_body.genotype import Genotype
from ..plasticoding.crossover.crossover import CrossoverConfig
from ..plasticoding.crossover.standard_crossover import standard_crossover
from .config import Config


def crossover(parents: List[Genotype], config: Config) -> Genotype:
    pars = Plasticize(parents, config)

    crossover_config = CrossoverConfig(
        config.crossover_prob, config.plasticoding_config
    )

    out = Deplasticize(standard_crossover({"plane": 0.03}, pars, crossover_config))
    return out


def Plasticize(parents, config):
    p = []
    for parent in parents:
        gen = Plasticoding(config.plasticoding_config)
        gen.grammar = parent.genotype_impl
        p.append(gen)
    return p


def Deplasticize(genotype):
    gen = Genotype(genotype_impl=genotype.grammar)
    return gen
