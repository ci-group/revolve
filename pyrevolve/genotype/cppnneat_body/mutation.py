from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype
from pyrevolve.genotype.cppnneat_body.config import CppnneatBodyConfig


def cppnneat_body_mutate(
    genotype: CppnneatGenotype, config: CppnneatBodyConfig
) -> CppnneatGenotype:
    copy = genotype.clone()
    copy.mutate(config.multineat_params, config.innov_db, config.rng)
    return copy
