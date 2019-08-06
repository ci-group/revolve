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

    @property
    def id(self):
        _id = None
        if self.phenotype is not None:
            _id = self.phenotype.id
        elif self.genotype.id is not None:
            _id = self.genotype.id
        return _id

    def export_genotype(self, folder):
        self.genotype.export_genotype(f'{folder}/genotypes/genotype_{self.phenotype.id}.txt')

    def export_phenotype(self, folder):
        if self.phenotype is not None:
            self.phenotype.save_file(f'{folder}/phenotypes/{self.phenotype.id}.yaml', conf_type='yaml')

    def export_fitness(self, folder):
        if self.fitness is not None:
            with open(f'{folder}/fitness_{self.id}.txt', 'w') as f:
                f.write(str(self.fitness))

    def export(self, folder):
        self.export_genotype(folder)
        self.export_phenotype(folder)
        self.export_fitness(folder)

    def __repr__(self):
        return f'Individual_{self.id}({self.fitness})'
