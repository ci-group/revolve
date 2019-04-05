from pyrevolve.evolution.population import PopulationConfig, Population
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.lsystem.mutation.mutation import MutationConfig
from pyrevolve.evolution.lsystem.mutation.standard_mutation import standard_mutation
from pyrevolve.evolution.lsystem.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.genotype import GenotypeConfig
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig

def dummy_mutate(genotype):
	return genotype


def dummy_crossover(parents):
	return parents[0]


def dummy_selection(individuals):
	return individuals[0]


def crossover_selection(individuals, selector, howmany:int):
	selected = []
	for i in range(howmany):
		selected.append(
			# selector(individuals)
			individuals[i]
		)
	return selected


def generational_population_management(old_individuals, new_individuals):
	assert(len(old_individuals) == len(new_individuals))
	return new_individuals


def steady_state_population_management(old_individuals, new_individuals, selector):
	pop_size = len(old_individuals)
	selection_pool = old_individuals + new_individuals # check this
	selected_individuals = []
	for _i in range(pop_size):
		selected = selector(selection_pool)
		selected_individuals.append(selected)

	return selected_individuals

# genotype_conf = GenotypeConfig(	
# 	e_max_groups = 3,
# 	axiom_w = 'C',
# 	i_iterations = 3,
# 	weight_min = -1,
# 	weight_max = 1,
# 	oscillator_param_min = 1,
# 	oscillator_param_max = 10,
# )

genotype_conf = PlasticodingConfig()

mutation_conf = MutationConfig(
	mutation_prob=0.8,
	genotype_conf=genotype_conf,
)

conf = PopulationConfig(
	population_size=10,
	genotype_constructor=random_initialization,
	genotype_conf=genotype_conf,
	mutation_operator=standard_mutation,
	mutation_conf=mutation_conf,
	crossover_operator=standard_crossover,
	selection=dummy_selection,
	parent_selection=lambda individuals: crossover_selection(individuals, dummy_selection, 2),
	population_management=lambda old, new: steady_state_population_management(old, new, dummy_selection),
	offspring_size=5,
)

population = Population(conf)
population.init_pop()
population.next_gen()
