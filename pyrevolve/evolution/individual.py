from __future__ import annotations
import os

from typing import TYPE_CHECKING

from pyrevolve import SDF

if TYPE_CHECKING:
    from typing import Optional, List, Union, Any
    from pyrevolve.revolve_bot import RevolveBot
    from pyrevolve.genotype import Genotype


class Individual:

    genotype: Genotype
    phenotype: Union[RevolveBot, List[RevolveBot]]
    fitness: Optional[float]
    parents: Optional[List[Individual]]
    objectives: List[Any]
    pose: SDF.math.Vector3

    def __init__(self,
                 genotype: Genotype,
                 phenotype: Optional[Union[RevolveBot, List[RevolveBot]]] = None,
                 pose: Optional[SDF.math.Vector3] = None):
        """
        Creates an Individual object with the given genotype and optionally the phenotype.

        :param genotype: genotype of the individual
        :param phenotype (optional): phenotype of the individual
        """
        self.genotype: Genotype = genotype
        self.phenotype: Union[RevolveBot, List[RevolveBot]] = phenotype
        self.fitness: Optional[float] = None
        self.parents: Optional[List[Individual]] = None
        self.objectives = []
        self.pose: SDF.math.Vector3 = SDF.math.Vector3(0, 0, 0) if pose is None else pose

    def clone(self) -> Individual:
        """
        Creates a cloned copy of this individual
        :return: a cloned copy of the individual
        """
        genotype = self.genotype.clone()
        genotype.id = self.id
        cloned_phenotype = None  # TODO if self.phenotype is None else self.phenotype.clone()

        other = Individual(
            genotype=genotype,
            phenotype=cloned_phenotype,
            pose=self.pose.copy()
        )

        other.fitness = self.fitness
        other.parents = self.parents

        return other

    def develop(self) -> None:
        """
        Develops genotype into an intermediate phenotype
        """
        if self.phenotype is None:
            self.phenotype = self.genotype.develop()
            self.phenotype.pose = self.pose

    @property
    def id(self) -> int:
        _id = None
        if self.phenotype is not None:
            if isinstance(self.phenotype, list):
                _id = self.phenotype[0].id
            else:
                _id = self.phenotype.id
        elif self.genotype.id is not None:
            _id = self.genotype.id
        return _id

    def export_genotype(self, folder: str) -> None:
        self.genotype.export_genotype(os.path.join(folder, f'genotype_{self.id}.txt'))

    def export_phenotype(self, folder: str) -> None:
        if self.phenotype is None:
            self.develop()
        if isinstance(self.phenotype, list):
            for i, alternative in enumerate(self.phenotype):
                alternative.save_file(os.path.join(folder, f'phenotype_{alternative.id}_{i}.yaml'), conf_type='yaml')
        else:
            self.phenotype.save_file(os.path.join(folder, f'phenotype_{self.phenotype.id}.yaml'), conf_type='yaml')

    def export_phylogenetic_info(self, folder: str) -> None:
        """
        Export phylogenetic information
        (parents and other possibly other information to build a phylogenetic tree)
        :param folder: folder where to save the information
        """
        if self.parents is not None:
            parents_ids: List[str] = [str(p.id) for p in self.parents]
            parents_ids_str = ",".join(parents_ids)
        else:
            parents_ids_str = 'None'

        filename = os.path.join(folder, f'parents_{self.id}.yaml')
        with open(filename, 'w') as file:
            file.write(f'parents:{parents_ids_str}')

    def export_fitness_single_file(self, folder: str) -> None:
        """
        It's saving the fitness into a file. The fitness can be a floating point number or None
        :param folder: folder where to save the fitness
        """
        with open(os.path.join(folder, f'fitness_{self.id}.txt'), 'w') as f:
            f.write(str(self.fitness))

    def export(self, folder: str) -> None:
        self.export_genotype(folder)
        self.export_phylogenetic_info(folder)
        self.export_phenotype(folder)
        self.export_fitness(folder)

    def __repr__(self) -> str:
        return f'Individual_{self.id}({self.fitness})'
