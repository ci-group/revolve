from .. import Genotype
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenome


class LSystemCPGHyperNEATGenotypeConfig:
    def __init__(self, plasticonfig_conf, neat_conf):
        self.plasticoding = plasticonfig_conf
        self.neat = neat_conf


class LSystemCPGHyperNEATGenotype(Genotype):
    def __init__(self, conf: LSystemCPGHyperNEATGenotypeConfig = None, robot_id=None):

        self.id = robot_id

        if conf is None:
            self._body_genome = None
            self._brain_genome = None

        else:
            assert robot_id is not None
            self._body_genome = random_initialization(conf.plasticoding, robot_id)
            self._brain_genome = NeatBrainGenome(conf.neat, robot_id)




    # override
    def clone(self):
        clone = LSystemCPGHyperNEATGenotype()
        clone._body_genome = self._body_genome.clone()
        clone._brain_genome = self._brain_genome.clone()

    def develop(self):
        """
        Develops the genome into a revolve_bot (proto-phenotype)

        :return: a RevolveBot instance
        :rtype: RevolveBot
        """

        phenotype = self._body_genome.develop()
        #phenotype._brain = None  #self._brain_genome.develop()  #Change : Function not yet defined
        return phenotype

    def export_genotype (self, filepath):
        """
        Connects to plasticoding expor_genotype function
        :param filepath: file to save the genotype file to
        :return:
        """

        self._body_genome.export_genotype(filepath)

