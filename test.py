from pyrevolve.evolution.population import PopulationConfig
from pyrevolve.evolution.individual import *
# from evolution.lsystem.mutation.standard_mutation import standard_mutation
from pyrevolve.evolution.lsystem.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.initialization import random_initialization

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