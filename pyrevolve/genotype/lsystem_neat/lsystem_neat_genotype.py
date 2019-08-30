from .. import Genotype
from ..plasticoding import Plasticoding
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenome


class LSystemCPGHyperNEATGenotypeConfig:
    def __init__(self, plasticonfig_conf, neat_conf):
        self.plasticoding = plasticonfig_conf
        self.neat = neat_conf


class LSystemCPGHyperNEATGenotype(Genotype):
    def __init__(self, conf: LSystemCPGHyperNEATGenotypeConfig = None, robot_id=None):
        if conf is None:
            self._body_genome = None
            self._brain_genome = None
        else:
            assert robot_id is not None
            self._body_genome = Plasticoding(conf.plasticoding, robot_id)
            self._brain_genome = NeatBrainGenome(conf.neat, 0)

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
        phenotype._brain = self._brain_genome.develop()
        return phenotype
