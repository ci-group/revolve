from pyrevolve.genotype.lsystem_cpg.cpg_brain import CPGBrainGenome
from pyrevolve.genotype.lsystem_cpg.lsystem_cpg_genotype import LSystemCPGGenotype
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import generate_child_genotype as PlasticodingCrossover


class CrossoverConfig:
    def __init__(self,
                 crossover_prob):
        """
        Creates a Crossover object that sets the configuration for the crossover operator

        :param crossover_prob: crossover probability
        """
        self.crossover_prob = crossover_prob


class CPGCrossoverConf:
    def __init__(self):
        self.mate_average = True
        self.interspecies_crossover = True


def standard_crossover(parents, lsystem_conf, crossover_conf):
    """
    Creates an child (individual) through crossover with two parents

    :param parents: Parents type Individual
    :param lsystem_conf: LSystemCPGHyperNEATGenotypeConfig type with config for NEAT and Plasticoding
    :param crossover_conf: CrossoverConfig for lsystem crossover type
    :return: brain and body crossover (Only body right now)
    """
    assert len(parents) == 2

    parents_body_genotype = [p.genotype._body_genome for p in parents]

    print("parents", parents)

    child_genotype = LSystemCPGGenotype()
    print("made child")

    new_body = PlasticodingCrossover(parents_body_genotype, lsystem_conf.plasticoding, crossover_conf)
    new_brain = CPGBrainGenome()

    child_genotype._body_genome = new_body
    child_genotype._brain_genome = new_brain

    return child_genotype
