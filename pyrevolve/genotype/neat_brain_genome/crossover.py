class NEATCrossoverConf:
    def __init__(self):
        self.mate_average = True
        self.interspecies_crossover = True


def standard_crossover(parent_individuals, genotype_conf, crossover_conf):
    """
    Creates an child (individual) through crossover with two parents

    :param parent_individuals: parent individuals to be used for crossover
    :param genotype_conf: NEAT genotype configuration object
    :param crossover_conf: NEAT genotype crossover configuration object
    :return: genotype result of the crossover
    """
    assert len(parent_individuals) == 2
    child_genotype = parent_individuals[0]

    mother = parent_individuals[0]
    father = parent_individuals[1]
    #child_genotype = mother.Mate(father,
                                 #crossover_conf.mate_average,
                                 #crossover_conf.interspecies_crossover,
                                 #genotype_conf.rng,
                                 #genotype_conf.multineat_params)
    return child_genotype
