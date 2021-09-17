from typing import List

from pyrevolve.genotype.plasticoding import Plasticoding

from ..lsystem_body.genotype import Genotype
from ..plasticoding.crossover.crossover import CrossoverConfig
from ..plasticoding.crossover.standard_crossover import standard_crossover
from .config import Config


def crossover(parents: List[Genotype], config: Config) -> Genotype:
    pars = plasticize(parents, config)

    crossover_config = CrossoverConfig(
        config.crossover_prob, config.plasticoding_config
    )

    out = deplasticize(standard_crossover({"plane": 0.03}, pars, crossover_config))
    return out


def plasticize(parents, config):
    p = []
    for parent in parents:
        gen = Plasticoding(config.plasticoding_config)
        gen.grammar = parent.genotype_impl
        p.append(gen)
    return p


def deplasticize(genotype):
    gen = Genotype(genotype_impl=genotype.grammar)
    return gen
