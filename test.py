from pyrevolve.evolution.population import PopulationConfig, Population
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.lsystem.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.genotype import GenotypeConfig

genotype_conf = GenotypeConfig(	
	e_max_groups = 3,
	axiom_w = 'C',
	i_iterations = 3,
	weight_min = -1,
	weight_max = 1,
	oscillator_param_min = 1,
	oscillator_param_max = 10,
)

def dummy_crossover(parents):
	return parents[0]

# genotype_constructor=lambda: random_initialization(genotype_conf), # Q: move the method param to population.py?

def dummy_selection(individuals):
	return individuals[0]

conf = PopulationConfig(
	population_size=5,
	genotype_constructor=random_initialization, # Q: move the method param to population.py?
	genotype_conf=genotype_conf,
	mutation_operator=standard_mutation,
	mutation_conf=mutation_conf,
	crossover_operator=dummy_crossover,
	selection=dummy_selection,
	parent_selection=lambda individuals: crossover_selection(individuals, dummy_selection, 2),
	population_management=lambda old, new: steady_state_population_management(old, new, dummy_selection),
)

population = Population(conf)
population.init_pop()
