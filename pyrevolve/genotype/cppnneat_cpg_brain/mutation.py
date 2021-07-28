from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype
from pyrevolve.genotype.cppnneat_cpg_brain.config import CppnneatCpgBrainConfig


def cppnneat_cpg_brain_mutate(
    genotype: CppnneatGenotype, config: CppnneatCpgBrainConfig
) -> CppnneatGenotype:
    copy = genotype.clone()
    copy.mutate(config.multineat_params, config.innov_db, config.rng)
    return copy
