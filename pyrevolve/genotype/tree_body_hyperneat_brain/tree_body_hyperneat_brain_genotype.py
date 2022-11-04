from __future__ import annotations

from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeGenotype
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenome, NeatBrainGenomeConfig
from .. import Genotype

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional, List, Union
    from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotypeConfig
    from pyrevolve.genotype.neat_brain_genome.crossover import NEATCrossoverConf
    from pyrevolve.revolve_bot import RevolveBot


class DirectTreeCPGHyperNEATGenotypeConfig:
    def __init__(self,
                 direct_tree_conf: DirectTreeGenotypeConfig,
                 neat_conf: NeatBrainGenomeConfig,
                 neat_crossover_conf: NEATCrossoverConf,
                 number_of_brains: int = 1):
        assert number_of_brains > 0
        self.direct_tree = direct_tree_conf
        self.number_of_brains: int = number_of_brains
        self.neat: NeatBrainGenomeConfig = neat_conf
        self.neat_crossover: NEATCrossoverConf = neat_crossover_conf


class DirectTreeCPGHyperNEATGenotype(Genotype):
    GENOME_SEPARATOR_TEXT = '--------GENOME-SEPARATOR--------\n'

    def __init__(self,
                 conf: Optional[DirectTreeCPGHyperNEATGenotypeConfig] = None,
                 robot_id: Optional[int] = None,
                 random_init_body: bool = True):

        self._id: int = robot_id

        self._brain_genomes: List[NeatBrainGenome] = []
        if conf is None:
            self._body_genome = None
        else:
            assert robot_id is not None
            self._body_genome: DirectTreeGenotype = DirectTreeGenotype(conf.direct_tree,
                                                                       robot_id,
                                                                       random_init=random_init_body)
            for _ in range(conf.number_of_brains):
                self._brain_genomes.append(NeatBrainGenome(conf.neat, robot_id))

    @property
    def id(self) -> int:
        return self._id

    def is_brain_compatible(self,
                            other: DirectTreeCPGHyperNEATGenotype,
                            conf: DirectTreeCPGHyperNEATGenotypeConfig) -> bool:
        """
        Test if all brains are compatible
        :param other: other genome to test against
        :param conf: Genome Configuration object
        :return: true if brains are compatible
        """
        if not isinstance(other, DirectTreeCPGHyperNEATGenotype):
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
            self._body_genome._export_genotype_open_file(f, onlyBody=True)
            # write the brain genomes
            for brain_genome in self._brain_genomes:
                f.write(DirectTreeCPGHyperNEATGenotype.GENOME_SEPARATOR_TEXT)
                brain_genome._export_genotype_open_file(f)

    def load_genotype(self, file_path: str) -> None:
        with open(file_path) as f:
            lines = f.readlines()
            # remove first element - it's the number of brain genomes
            number_of_brain_genomes = int(lines.pop(0))

            # search for genome segments
            separators = []
            for i, line in enumerate(lines):
                if line == DirectTreeCPGHyperNEATGenotype.GENOME_SEPARATOR_TEXT:
                    separators.append(i)
            assert len(separators) > 0

            # read the body genome
            self._body_genome._load_genotype_from_lines(lines[:separators[0]], only_body=True)

            # read the brain genomes
            assert len(separators) == number_of_brain_genomes
            separators.append(len(lines))
            for i in range(number_of_brain_genomes):
                text = ''.join(lines[separators[i]+1:separators[i+1]]).strip()
                self._brain_genomes[i]._load_genotype_from(text)

    def clone(self) -> DirectTreeCPGHyperNEATGenotype:
        clone = DirectTreeCPGHyperNEATGenotype()
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
        for i, brain_genome in enumerate(self._brain_genomes):
            phenotype: RevolveBot = self._body_genome.develop()
            _id = phenotype._id
            if type(_id) == int:
                phenotype._id += i * 10000000
            elif type(_id) == str:
                phenotype._id = str(int(_id) + i * 10000000)
            else:
                raise RuntimeError(f"unsupported ID type {type(_id)}")

            phenotype._brain = brain_genome.develop()
            phenotypes.append(phenotype)

        if len(phenotypes) == 1:
            return phenotypes[0]
        else:
            return phenotypes
