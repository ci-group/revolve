from typing import List

from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype
from pyrevolve.genotype.cppnneat_body.config import CppnneatBodyConfig


def cppnneat_body_crossover(
    parents: List[CppnneatGenotype], config: CppnneatBodyConfig
) -> CppnneatGenotype:
    assert len(parents) == 2
    return parents[0].mate(parents[1], config.multineat_params, config.rng)
