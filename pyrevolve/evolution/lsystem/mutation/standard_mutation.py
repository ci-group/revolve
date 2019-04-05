import random
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet, Plasticoding

def handle_deletion(genotype):
	# print('-------delete----------')
	target_production_rule = random.choice(list(genotype.grammar))
	# print('target production rule: \n')
	# print(target_production_rule)
	# print('\n')
	if (len(genotype.grammar[target_production_rule])) > 1:
		# print('Length of production rule was larger than 1!\n')
		symbol_to_delete = random.choice(genotype.grammar[target_production_rule])
		# print('Symbol to delete: \n')
		# print(symbol_to_delete)
		# print('\n')
		if symbol_to_delete[0] != Alphabet.CORE_COMPONENT:
			# print('Symbol to delete was not a core component!\n')
			genotype.grammar[target_production_rule].remove(symbol_to_delete)
	# print('\n\n')
	return genotype

def handle_swap(genotype):
	# print('-------swap----------')
	target_production_rule = random.choice(list(genotype.grammar))
	if (len(genotype.grammar[target_production_rule])) > 1:
		# print('')
		symbols_to_swap = random.choices(population=genotype.grammar[target_production_rule], k=2)
		for symbol in symbols_to_swap:
			if symbol[0] == Alphabet.CORE_COMPONENT:
				return genotype
		item_index_1 = genotype.grammar[target_production_rule].index(symbols_to_swap[0])
		item_index_2 = genotype.grammar[target_production_rule].index(symbols_to_swap[1])
		genotype.grammar[target_production_rule][item_index_2], genotype.grammar[target_production_rule][item_index_1] = genotype.grammar[target_production_rule][item_index_1], genotype.grammar[target_production_rule][item_index_2]

	return genotype

def generate_symbol(genotype_conf):
	symbol_category = random.randint(1,5)
	# Modules
	if symbol_category == 1:
		alphabet = random.randint(1,len(Alphabet.modules())-1)
		symbol = Plasticoding.build_symbol(Alphabet.modules()[alphabet], genotype_conf)
	# Morphology mounting commands
	elif symbol_category == 2: 
		alphabet = random.randint(0,len(Alphabet.morphology_mounting_commands())-1)
		symbol = Plasticoding.build_symbol(Alphabet.morphology_mounting_commands()[alphabet], genotype_conf)
	# Morphology moving commands
	elif symbol_category == 3:
		alphabet = random.randint(0,len(Alphabet.morphology_moving_commands())-1)
		symbol = Plasticoding.build_symbol(Alphabet.morphology_moving_commands()[alphabet], genotype_conf)
	# Controller moving commands
	elif symbol_category == 4:
		alphabet = random.randint(0,len(Alphabet.controller_moving_commands())-1)
		symbol = Plasticoding.build_symbol(Alphabet.controller_moving_commands()[alphabet], genotype_conf)
	# Controller changing commands
	elif symbol_category == 5:
		alphabet = random.randint(0,len(Alphabet.controller_changing_commands())-1)
		symbol = Plasticoding.build_symbol(Alphabet.controller_changing_commands()[alphabet], genotype_conf)
	else:
		raise Exception('random number did not generate a number between 1 and 5. The value was: {}'.format(symbol_category))

	return symbol


def handle_addition(genotype, genotype_conf):
	print('addition')
	target_production_rule = random.choice(list(genotype.grammar))
	if target_production_rule == Alphabet.CORE_COMPONENT:
		addition_index = random.randint(1,len(genotype.grammar[target_production_rule])-1)
	else:
		addition_index = random.randint(0,len(genotype.grammar[target_production_rule])-1)
	symbol_to_add = generate_symbol(genotype_conf)
	genotype.grammar[target_production_rule].insert(addition_index,symbol_to_add)

	return genotype

def standard_mutation(genotype, mutation_conf):
	new_genotype = genotype.clone()
	chance_of_mutation = random.uniform(0.0,1.0)
	if chance_of_mutation <= mutation_conf.mutation_prob:
		return new_genotype
	else:
		mutation_type = random.randint(1,3) # NTS: better way?
		if mutation_type == 1:
			modified_genotype = handle_deletion(new_genotype)
		elif mutation_type == 2:
			modified_genotype = handle_swap(new_genotype)
		elif mutation_type == 3:
			modified_genotype = handle_addition(new_genotype, mutation_conf.genotype_conf)
		else:
			raise Exception('mutation_type value was not in the expected range (1,3). The value was: {}'.format(mutation_type))
		# print('Modified genotype: \n')
		# print(modified_genotype.grammar)
		# print('\n\n')
		return modified_genotype
