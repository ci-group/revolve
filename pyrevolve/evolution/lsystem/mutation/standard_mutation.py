import random

def handle_deletion():
	print("deletion")

def handle_replacement():
	print("replacement")

def handle_addition():
	print("addition")

def standard_mutation(genotype, mutation_conf):
	print(genotype.grammar)
	print("\n\n")
	chance_of_mutation = random.uniform(0.0,1.0)
	if chance_of_mutation <= mutation_conf.mutation_prob:
		return genotype
	else:
		mutation_type = random.randint(1,3) # NTS: better way?
		if mutation_type == 1:
			handle_deletion()
		elif mutation_type == 2:
			handle_replacement()
		elif mutation_type == 3:
			handle_addition()
		else:
			raise Exception('mutation_type value was not in the expected range (1,3). The value was: {}'.format(mutation_type))

		return genotype

