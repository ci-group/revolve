import os

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional, List
    from pyrevolve.revolve_bot import RevolveBot
    from pyrevolve.genotype import Genotype


class Individual:

    def __init__(self, genotype: Genotype, phenotype: Optional[RevolveBot] = None):

        """
        Creates an Individual object with the given genotype and optionally the phenotype.

        :param genotype: genotype of the individual
        :param phenotype (optional): phenotype of the individual
        """
        self.genotype: Genotype = genotype
        self.phenotype: RevolveBot = phenotype
        self.fitness: Optional[float] = None
        self.parents: Optional[List[Individual]] = None
        self.failed_eval_attempt_count: int = 0

    # TODO make genotype, phenotype and other properties private.
    def develop(self):
        """
        Develops genotype into a intermediate phenotype
        """
        if self.phenotype is None:
            self.phenotype = self.genotype.develop()

    # TODO is this needed to be recalculated each time, could be set in the constructor and
    #  in the develop function if after the phenotype is set.
    @property
    def id(self):
        _id = None
        if self.phenotype is not None:
            _id = self.phenotype.id
        elif self.genotype.id() is not None:
            _id = self.genotype.id()
        return _id

    # TODO refactor to momento
    def _export_genotype(self, folder: str):
        if self.genotype is not None:
            # TODO should be yaml?
            # TODO should this be phenotype?
            self.genotype.export_genotype(f'{folder}/genotypes/genotype_{self.genotype.id()}.txt')

    # TODO refactor to momento
    def _export_phenotype(self, folder: str):
        if self.phenotype is not None:
            # TODO "/phenotypes/phenotype_"
            self.phenotype.save_file(f'{folder}/phenotypes/{self.phenotype.id}.yaml', conf_type='yaml')

    # TODO refactor to momento
    def _export_fitness(self, folder: str):
        """
        It's saving the fitness into a file. The fitness can be a floating point number or None
        :param folder: folder where to save the fitness
        """
        with open(f'{folder}/fitness_{self.id}.txt', 'w') as f:
            f.write(str(self.fitness))

    # TODO refactor to momento
    def export(self, folder : str):
        if folder is not None:
            self._export_genotype(folder)
            self._export_phenotype(folder)
            self._export_fitness(folder)

    def __repr__(self):
        return f'Individual_{self.id}({self.fitness})'

def create_individual(experiment_management, genotype: Genotype):
    individual = Individual(genotype)
    individual.develop()
    individual.phenotype.update_substrate()
    experiment_management.export_genotype(individual)
    experiment_management.export_phenotype(individual)
    experiment_management.export_phenotype_images(os.path.join('data_fullevolution', 'phenotype_images'), individual)
    individual.phenotype.measure_phenotype()
    individual.phenotype.export_phenotype_measurements(experiment_management.data_folder)

    return individual
