from .. import Genotype
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenome

from pyrevolve.util.robot_identifier import RobotIdentifier

class LSystemCPGHyperNEATGenotypeConfig:
    def __init__(self, plasticonfig_conf, neat_conf):
        self.plasticoding = plasticonfig_conf
        self.neat = neat_conf


class LSystemCPGHyperNEATGenotype(Genotype):
    def __init__(self, conf: LSystemCPGHyperNEATGenotypeConfig = None):

        super().__init__()

        if conf is None:
            self._body_genome = None
            self._brain_genome = None
        else:
            self._body_genome = random_initialization(conf.plasticoding, self._id)
            self._brain_genome = NeatBrainGenome(conf.neat, self._id)

    @id.setter
    def id(self, value):
        self._id = value
        self._body_genome.id = value
        self._brain_genome.id = value

    def load_genotype(self, file_path: str):
        with open(file_path) as f:
            lines = f.readlines()
            self._body_genome._load_genotype_from(lines[:-1])
            self._brain_genome._load_genotype_from(lines[-1])

    def clone(self):
        clone = LSystemCPGHyperNEATGenotype()
        clone._body_genome = self._body_genome.clone()
        clone._brain_genome = self._brain_genome.clone()
        return clone

    def develop(self):
        """
        Develops the genome into a revolve_bot (proto-phenotype)

        :return: a RevolveBot instance
        :rtype: RevolveBot
        """

        phenotype = self._body_genome.develop()
        phenotype._brain = self._brain_genome.develop()
        return phenotype

    def export_genotype(self, file_path: str):
        """
        Connects to plasticoding expor_genotype function
        :param file_path: file to save the genotype file to
        :return:
        """
        with open(file_path, 'w+') as f:
            self._body_genome._export_genotype_open_file(f)
            self._brain_genome._export_genotype_open_file(f)

