from pyrevolve.angle.robogen import Config
from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeMutationConfig
from pyrevolve.genotype.direct_tree.direct_tree_crossover import DirectTreeCrossoverConfig, Crossover
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenomeConfig
from pyrevolve.genotype.direct_tree.direct_tree_mutation import Mutator
from pyrevolve.tol.spec import get_tree_generator

body_conf = DirectTreeGenomeConfig()

config = Config(5, 10, 3, 6)
robogen_tree_generator: RobogenTreeGenerator = get_tree_generator(config)

tree_mutation_conf = DirectTreeMutationConfig()
mutation = Mutator(robogen_tree_generator)

tree_crossover_conf = DirectTreeCrossoverConfig()
tree_crossover = Crossover(robogen_tree_generator)

