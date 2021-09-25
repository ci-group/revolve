from typing import List

from pyrevolve.genotype.plasticoding import Plasticoding

from ..lsystem_body.genotype import Genotype
from ..plasticoding.crossover.crossover import CrossoverConfig
from ..plasticoding.crossover.standard_crossover import standard_crossover
from .config import Config


def crossover(parents: List[Genotype], config: Config) -> Genotype:
    pars = plasticize(parents, config)
    crossover_config = CrossoverConfig(
        config.crossover_prob,
        config.plasticoding_config,
    )
    out = standard_crossover(pars, crossover_config.genotype_conf, crossover_config)

    gen = Genotype(genotype_impl=out.grammar)

    return gen


def plasticize(parents, config):
    p = []
    for parent in parents:

        gen = Plasticoding(config.plasticoding_config,robot_id=0)
        gen.grammar = parent.genotype_impl
        p.append(gen)
    return p


def deplasticize(genotype):
    gen = Genotype(genotype_impl=genotype.grammar)
    return gen
