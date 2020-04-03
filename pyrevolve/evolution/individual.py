from __future__ import annotations
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

    def develop(self) -> None:
        """
        Develops genotype into a intermediate phenotype
        """
        if self.phenotype is None:
            self.phenotype = self.genotype.develop()

    @property
    def id(self) -> int:
        _id = None
        if self.phenotype is not None:
            _id = self.phenotype.id
        elif self.genotype.id is not None:
            _id = self.genotype.id
        return _id

    def export_genotype(self, folder) -> None:
        self.genotype.export_genotype(os.path.join(folder, f'genotype_{self.phenotype.id}.txt'))

    def export_phenotype(self, folder) -> None:
        if self.phenotype is None:
            self.develop()
        self.phenotype.save_file(os.path.join(folder, f'phenotype_{self.phenotype.id}.yaml'), conf_type='yaml')

    def export_fitness(self, folder) -> None:
        """
        It's saving the fitness into a file. The fitness can be a floating point number or None
        :param folder: folder where to save the fitness
        """
        with open(os.path.join(folder, f'fitness_{self.id}.txt'), 'w') as f:
            f.write(str(self.fitness))

    def export(self, folder) -> None:
        self.export_genotype(folder)
        self.export_phenotype(folder)
        self.export_fitness(folder)

    def __repr__(self) -> str:
        return f'Individual_{self.id}({self.fitness})'
