import sys
import xml.etree.ElementTree
import multineat

from .cppn_cpg import BrainCPPNCPG


# Extends BrainCPG by including a Genome
class BrainCPPNCPGTarget(BrainCPPNCPG):
    TYPE = 'cppn-cpg-target'

    def __init__(self, neat_genome):
        super().__init__(neat_genome)

    def learner_sdf(self):
        return xml.etree.ElementTree.Element('rv:learner', {
            'type': 'target',
        })
