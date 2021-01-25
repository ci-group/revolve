from pyrevolve.angle.robogen import Config
from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from pyrevolve.genotype.direct_tree.compound_mutation import DirectTreeNEATMutationConfig
from pyrevolve.genotype.direct_tree.direct_tree_crossover import DirectTreeCrossoverConfig, Crossover
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenomeConfig, DirectTreeGenome
from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeNEATGenotype, \
    DirectTreeNEATGenotypeConfig
from pyrevolve.genotype.direct_tree.tree_mutation import Mutator, DirectTreeMutationConfig
from pyrevolve.genotype.neat_brain_genome import NeatBrainGenomeConfig
from pyrevolve.tol.spec import get_tree_generator

config = Config(min_parts=5,
                max_parts=10,
                max_inputs=3,
                max_outputs=6,
                disable_sensors=True,
                enable_touch_sensor=False)
robogen_tree_generator: RobogenTreeGenerator = get_tree_generator(config)

body_conf = DirectTreeGenomeConfig()
tree1 = DirectTreeGenome(body_conf, 0)
tree2 = DirectTreeGenome(body_conf, 1)

#         #

tree_crossover_conf = DirectTreeCrossoverConfig()
tree_crossover = Crossover(robogen_tree_generator)

brain_conf = NeatBrainGenomeConfig()
genome_config = DirectTreeNEATGenotypeConfig(body_conf, brain_conf)

genome1 = DirectTreeNEATGenotype(genome_config, 2)
genome2 = DirectTreeNEATGenotype(genome_config, 3)

tree_mutation_conf = DirectTreeMutationConfig()
tree_mutation_neat_config = DirectTreeNEATMutationConfig(tree_mutation_conf, brain_conf)

mutation = Mutator(robogen_tree_generator)
genome3 = mutation.mutate(genome1, tree_mutation_neat_config)
genome4 = mutation.mutate(genome1, tree_mutation_neat_config)

parents = [genome1, genome2]

genome5 = tree_crossover.crossover(parents, genome_config, tree_crossover_conf)