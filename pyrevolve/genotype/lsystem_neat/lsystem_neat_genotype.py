from __future__ import annotations

from .. import Genotype
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenome, NeatBrainGenomeConfig

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional, List, Union
    from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding, PlasticodingConfig
    from pyrevolve.revolve_bot import RevolveBot


class LSystemCPGHyperNEATGenotypeConfig:
    def __init__(self,
                 plasticonfig_conf: PlasticodingConfig,
                 neat_conf: NeatBrainGenomeConfig,
                 number_of_brains: int = 1):
        assert number_of_brains > 0
        self.plasticoding = plasticonfig_conf
        self.number_of_brains: int = number_of_brains
        self.neat: NeatBrainGenomeConfig = neat_conf


class LSystemCPGHyperNEATGenotype(Genotype):
    def __init__(self, conf: Optional[LSystemCPGHyperNEATGenotypeConfig] = None, robot_id: Optional[int] = None):

        self._id: int = robot_id

        self._brain_genomes = []
        if conf is None:
            self._body_genome = None
        else:
            assert robot_id is not None
            self._body_genome: Plasticoding = random_initialization(conf.plasticoding, robot_id)
            for _ in range(conf.number_of_brains):
                self._brain_genomes.append(NeatBrainGenome(conf.neat, robot_id))

    @property
    def id(self) -> int:
        return self._id

    def is_brain_compatible(self,
                            other: LSystemCPGHyperNEATGenotype,
                            conf: LSystemCPGHyperNEATGenotypeConfig) -> bool:
        """
        Test if all brains are compatible
        :param other: other genome to test against
        :param conf: Genome Configuration object
        :return: true if brains are compatible
        """
        if not isinstance(other, LSystemCPGHyperNEATGenotype):
            return False
        if len(self._brain_genomes) != len(other._brain_genomes):
            return False
        for self_brain, other_brain in zip(self._brain_genomes, other._brain_genomes):
            if not self_brain.is_compatible(other_brain, conf.neat):
                return False

        return True

    @id.setter
    def id(self, value) -> None:
        self._id = value
        self._body_genome.id = value
        for brain_genome in self._brain_genomes:
            # WARNING! multiple genomes with the same id?
            brain_genome.id = value

    def export_genotype(self, file_path: str) -> None:
        """
        Connects to plasticoding expor_genotype function
        :param file_path: file to save the genotype file to
        """
        with open(file_path, 'w+') as f:
            # the first element is the number of brain genomes
            f.write(f'{len(self._brain_genomes)}\n')
            # write the body genome
            self._body_genome._export_genotype_open_file(f)
            # write the brain genomes
            for brain_genome in self._brain_genomes:
                brain_genome._export_genotype_open_file(f)

    def load_genotype(self, file_path: str) -> None:
        with open(file_path) as f:
            lines = f.readlines()
            # remove first element - it's the number of brain genomes
            number_of_brain_genomes = int(lines.pop(0))
            # read the body genome
            self._body_genome._load_genotype_from(lines[:-number_of_brain_genomes])
            # read the brain genomes
            for brain_i in range(number_of_brain_genomes):
                i = -number_of_brain_genomes + brain_i
                self._brain_genomes[brain_i]._load_genotype_from(lines[i].strip())

    def clone(self) -> LSystemCPGHyperNEATGenotype:
        clone = LSystemCPGHyperNEATGenotype()
        clone._body_genome = self._body_genome.clone()
        clone._brain_genomes = []
        for brain_genome in self._brain_genomes:
            clone._brain_genomes.append(brain_genome.clone())
        return clone

    def develop(self) -> Union[RevolveBot, List[RevolveBot]]:
        """
        Develops the genome into a (series of) revolve_bot (proto-phenotype)
        :return: one/many RevolveBot instance(s)
        """
        phenotypes = []
        for i,brain_genome in enumerate(self._brain_genomes):
            phenotype: RevolveBot = self._body_genome.develop()
            phenotype._id += i*10000000
            phenotype._brain = brain_genome.develop()
            phenotypes.append(phenotype)

        if len(phenotypes) == 1:
            return phenotypes[0]
        else:
            return phenotypes
