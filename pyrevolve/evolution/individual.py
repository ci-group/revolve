# (G,P)


class Individual:
    def __init__(self, genotype, phenotype=None):
        """
        Creates an Individual object with the given genotype and optionally the phenotype.

        :param genotype: genotype of the individual
        :param phenotype (optional): phenotype of the individual
        """
        self.genotype = genotype
        self.phenotype = phenotype
        self.fitness = None
        self.parents = None
        self.failed_eval_attempt_count = 0

    def develop(self):
        """
        Develops genotype into a intermediate phenotype

        """
        if self.phenotype is None:
            self.phenotype = self.genotype.develop()

    def __repr__(self):
        _id = None
        if self.phenotype is not None:
            _id = self.phenotype.id
        elif self.genotype.id is not None:
            _id = self.genotype.id
        return f'Individual_{_id}({self.fitness})'

