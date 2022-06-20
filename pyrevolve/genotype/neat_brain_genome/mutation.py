import multineat
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from genotype.plasticoding.mutation.mutation import MutationConfig


def _mutation(genotype, baby_is_clone: bool, search_mode: multineat.SearchMode, genotype_conf: MutationConfig):
    new_genotype = genotype.clone()
    if genotype_conf.apply_constraints:
        new_genotype._neat_genome = new_genotype._neat_genome.MutateWithConstraints(
            baby_is_clone,
            search_mode,
            genotype_conf.innov_db,
            genotype_conf.multineat_params,
            genotype_conf.rng
        )
    else:
        new_genotype._neat_genome.Mutate(
            baby_is_clone,
            search_mode,
            genotype_conf.innov_db,
            genotype_conf.multineat_params,
            genotype_conf.rng
        )
    return new_genotype


def mutation_complexify(genotype, genotype_conf):
    return _mutation(genotype, False, multineat.SearchMode.COMPLEXIFYING, genotype_conf)


def mutation_simplify(genotype, genotype_conf):
    return _mutation(genotype, False, multineat.SearchMode.SIMPLIFYING, genotype_conf)


def mutation_blended(genotype, genotype_conf):
    return _mutation(genotype, False, multineat.SearchMode.BLENDED, genotype_conf)
