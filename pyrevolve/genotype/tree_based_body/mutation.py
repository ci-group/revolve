from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype
from pyrevolve.genotype.direct_tree.direct_tree_mutation import DirectTreeMutationConfig as MutationConfig
from pyrevolve.genotype.direct_tree.direct_tree_mutation import mutate as Tmutate

from .config import Config
from .genotype import Genotype


def mutate(genotype: Genotype, config: Config) -> Genotype:
    #gen = DirectTreeGenotype(config.directtree_config,robot_id=0)
    #gen = genotype.genotype_impl

    mutation_config = MutationConfig
    mutatedgenotype = Tmutate(genotype.genotype_impl, config)

    copy = genotype.clone()
    copy.genotype_impl = mutatedgenotype.genotype_impl

    return copy
