import random

def standard_mutation(genotype, mutation_conf):
	chance_of_mutation = random.uniform()
	if chance_of_mutation <= mutation_conf.mutation_prob:
		return genotype
	else:
		mutation_type = random.randint(1,3) # NTS: better way?
		

