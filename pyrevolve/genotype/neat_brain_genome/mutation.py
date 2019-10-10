import multineat


def _mutation(genotype, baby_is_clone: bool, search_mode: multineat.SearchMode, genotype_conf):
    new_genotype = genotype.genotype._brain_genome.clone()
    new_genotype._neat_genome.Mutate(
        baby_is_clone,
        search_mode,
        genotype_conf.innov_db,
        genotype_conf.multineat_params,
        genotype_conf.rng
    )
    return new_genotype


def mutation_complexify(genotype, genotype_conf):
    _mutation(genotype, False, multineat.SearchMode.COMPLEXIFYING, genotype_conf)


def mutation_simplify(genotype, genotype_conf):
    _mutation(genotype, False, multineat.SearchMode.SIMPLIFYING, genotype_conf)
