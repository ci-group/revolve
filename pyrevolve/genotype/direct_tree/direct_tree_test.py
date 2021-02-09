#TODO remove these
from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from pyrevolve.tol.spec import get_tree_generator

from pyrevolve.genotype.direct_tree import DirectTreeConfig
from pyrevolve.genotype.direct_tree.compound_mutation import DirectTreeNEATMutationConfig
from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeMutationConfig
from pyrevolve.genotype.direct_tree.direct_tree_crossover import DirectTreeCrossoverConfig, Crossover
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype
from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeNEATGenotype, \
    DirectTreeNEATGenotypeConfig
from pyrevolve.genotype.direct_tree.tree_mutation import Mutator
from pyrevolve.genotype.neat_brain_genome import NeatBrainGenomeConfig

config = DirectTreeConfig(min_parts=5, max_parts=11, max_inputs=3, max_outputs=6,
                          initial_parts_mu=8, initial_parts_sigma=1.5,
                          disable_sensors=True, enable_touch_sensor=False)
tree_crossover_conf = DirectTreeCrossoverConfig()
brain_conf = NeatBrainGenomeConfig()
genome_config = DirectTreeNEATGenotypeConfig(config, brain_conf)
tree_mutation_conf = DirectTreeMutationConfig()

# what is this?
robogen_tree_generator: RobogenTreeGenerator = get_tree_generator(config)

# create two robot genomes (direct only)
genome1 = DirectTreeGenotype(config, 0)
genome2 = DirectTreeGenotype(config, 1)

print(genome1.representation.root.__class__)
print(genome2.representation.root.__class__)

# genome mutation
mutation = Mutator(robogen_tree_generator)
genome3 = mutation.mutate(genome1, tree_mutation_conf, False)
genome4 = mutation.mutate(genome1, tree_mutation_conf, False)

print(genome3.id, genome3.representation.root, genome3.representation.root)
print(genome4.id, genome4.representation.root, genome4.representation.root)

# crossover
tree_crossover = Crossover(robogen_tree_generator)
parents = [genome1, genome2]
genome5 = tree_crossover.crossover(parents, genome_config, tree_crossover_conf)

print(genome5.id, genome5.representation.root, genome5.representation.root)

# TODO decoding into revolve_bot
