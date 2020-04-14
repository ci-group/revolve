from __future__ import annotations

from .. import Genotype
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenome, NeatBrainGenomeConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional
    from pyrevolve.revolve_bot import RevolveBot


class LSystemCPGHyperNEATGenotypeConfig:
    def __init__(self, plasticonfig_conf, neat_conf: NeatBrainGenomeConfig):
        self.plasticoding = plasticonfig_conf
        self.neat: NeatBrainGenomeConfig = neat_conf


class LSystemCPGHyperNEATGenotype(Genotype):
    def __init__(self, conf: Optional[LSystemCPGHyperNEATGenotypeConfig] = None, robot_id: Optional[int] = None):

        self._id: int = robot_id

        if conf is None:
            self._body_genome = None
            self._brain_genome = None
        else:
            assert robot_id is not None
            self._body_genome: Plasticoding = random_initialization(conf.plasticoding, robot_id)
            self._brain_genome = NeatBrainGenome(conf.neat, robot_id)

    @property
    def id(self) -> int:
        return self._id

    def is_brain_compatible(self,
                            other: LSystemCPGHyperNEATGenotype,
                            conf: LSystemCPGHyperNEATGenotypeConfig) -> bool:
        return isinstance(other, LSystemCPGHyperNEATGenotype) \
               and self._brain_genome.is_compatible(other._brain_genome, conf.neat)

    @id.setter
    def id(self, value) -> None:
        self._id = value
        self._body_genome.id = value
        self._brain_genome.id = value

    def load_genotype(self, file_path: str) -> None:
        with open(file_path) as f:
            lines = f.readlines()
            self._body_genome._load_genotype_from(lines[:-1])
            self._brain_genome._load_genotype_from(lines[-1])

    def clone(self) -> LSystemCPGHyperNEATGenotype:
        clone = LSystemCPGHyperNEATGenotype()
        clone._body_genome = self._body_genome.clone()
        clone._brain_genome = self._brain_genome.clone()
        return clone

    def develop(self) -> RevolveBot:
        """
        Develops the genome into a revolve_bot (proto-phenotype)
        :return: a RevolveBot instance
        """
        phenotype = self._body_genome.develop()
        phenotype._brain = self._brain_genome.develop()
        return phenotype

    def export_genotype(self, file_path: str) -> None:
        """
        Connects to plasticoding expor_genotype function
        :param file_path: file to save the genotype file to
        """
        with open(file_path, 'w+') as f:
            self._body_genome._export_genotype_open_file(f)
            self._brain_genome._export_genotype_open_file(f)
