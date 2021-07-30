from typing import List

from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype
from pyrevolve.genotype.cppnneat_cpg_brain.config import CppnneatCpgBrainConfig


def cppnneat_cpg_brain_crossover(
    parents: List[CppnneatGenotype], config: CppnneatCpgBrainConfig
) -> CppnneatGenotype:
    assert len(parents) == 2
    return parents[0].mate(parents[1], config.multineat_params, config.rng, config.mate_average, config.interspecies_crossover)
