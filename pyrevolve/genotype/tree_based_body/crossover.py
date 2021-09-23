from typing import List

from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype

from pyrevolve.genotype.tree_based_body.genotype import Genotype
from pyrevolve.genotype.direct_tree.direct_tree_crossover import crossover as standard_crossover
from .config import Config

def crossover(parents: List[Genotype], config: Config) -> Genotype:
    #pars = plasticize(parents, config)

    #crossover_config = CrossoverConfig(
    #    config.crossover_prob,
    #    config.plasticoding_config,
    #)
    out = standard_crossover(parents[0].genotype_impl,parents[1].genotype_impl,config,0)

#    gen = Genotype(genotype_impl=out.grammar)

    return out


def plasticize(parents, config):
    p = []
    for parent in parents:
        gen = DirectTreeGenotype(config.plasticoding_config,robot_id=0)
        gen.grammar = parent.genotype_impl
        p.append(gen)
    return p


def deplasticize(genotype):
    gen = Genotype(genotype_impl=genotype.grammar)
    return gen
