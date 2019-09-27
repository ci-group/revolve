def standard_crossover(parent_individuals):
    """
    Creates an child (individual) through crossover with two parents

    :param parent_individuals: parent individuals to be used for crossover
    :return: genotype result of the crossover
    """
    assert len(parent_individuals) == 2
    mother = parent_individuals[0].genotype
    father = parent_individuals[1].genotype
    child_genotype = mother.Mate(father, True, True, mother._conf.rng, mother._conf.multineat_params)
    return child_genotype
