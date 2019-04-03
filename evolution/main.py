from population import *
from individual import *
import lsystem.mutation.standard_mutation as standard_mutation

genotype_conf = {}

# conf = PopulationConfig(
# 	population_size=100,
# 	genotype_constructor=lambda: LSystemGenotype(genotype_conf),
# 	mutation_operator=standard_mutation,
# 	crossover_operator=dummy_crossover,
# 	selection=dummy_selection,
# 	parent_selection=lambda individuals: crossover_selection(individuals, dummy_selection, 2),
# 	population_management=lambda old, new: steady_state_population_management(old, new, dummy_selection),
# )

conf = PopulationConfig(
	population_size=100,
	genotype_constructor=lambda: LSystemGenotype(genotype_conf),
	mutation_operator=standard_mutation,
	crossover_operator=dummy_crossover,
	selection=dummy_selection,
	parent_selection=lambda individuals: crossover_selection(individuals, dummy_selection, 2),
	population_management=lambda old, new: steady_state_population_management(old, new, dummy_selection),
)

population = Population(conf)
population.init_pop()
