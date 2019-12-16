import random
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet, Plasticoding
from ....custom_logging.logger import genotype_logger
import sys



def handle_deletion(genotype):
    """
    Deletes symbols from genotype

    :param genotype: genotype to be modified

    :return: genotype
    """

    target_letter = random.choice(list(genotype.grammar))
    target_clause = random.choice(range(0, len(genotype.grammar[target_letter])))

    if (len(genotype.grammar[target_letter][target_clause][1])) > 1:
        symbol_to_delete = random.choice(genotype.grammar[target_letter][target_clause][1])
        if symbol_to_delete[0] != Alphabet.CORE_COMPONENT:
            genotype.grammar[target_letter][target_clause][1].remove(symbol_to_delete)
            genotype_logger.info(
                f'mutation: remove in {genotype.id} for {target_letter} in {target_clause} at {symbol_to_delete[0]}.')
    return genotype


def handle_swap(genotype):
    """
    Swaps symbols within the genotype

    :param genotype: genotype to be modified

    :return: genotype
    """

    target_letter = random.choice(list(genotype.grammar))
    target_clause = random.choice(range(0, len(genotype.grammar[target_letter])))

    if (len(genotype.grammar[target_letter][target_clause][1])) > 1:
        symbols_to_swap = random.choices(population=genotype.grammar[target_letter][target_clause][1], k=2)
        for symbol in symbols_to_swap:
            if symbol[0] == Alphabet.CORE_COMPONENT:
                return genotype
        item_index_1 = genotype.grammar[target_letter][target_clause][1].index(symbols_to_swap[0])
        item_index_2 = genotype.grammar[target_letter][target_clause][1].index(symbols_to_swap[1])
        genotype.grammar[target_letter][target_clause][1][item_index_2], genotype.grammar[target_letter][target_clause][1][item_index_1] = \
            genotype.grammar[target_letter][target_clause][1][item_index_1], genotype.grammar[target_letter][target_clause][1][item_index_2]
        genotype_logger.info(
            f'mutation: swap in {genotype.id} for {target_letter} in {target_clause} between {symbols_to_swap[0]} and {symbols_to_swap[1]}.')
    return genotype


def generate_symbol(genotype_conf):
    """
    Generates a symbol for addition

    :param genotype_conf: configuration for the genotype

    :return: symbol
    """
    symbol_category = random.randint(1, 5)
    # Modules
    if symbol_category == 1:
        alphabet = random.randint(1, len(Alphabet.modules()) - 1)
        symbol = Plasticoding.build_symbol(Alphabet.modules()[alphabet], genotype_conf)
    # Morphology mounting commands
    elif symbol_category == 2:
        alphabet = random.randint(0, len(Alphabet.morphology_mounting_commands()) - 1)
        symbol = Plasticoding.build_symbol(Alphabet.morphology_mounting_commands()[alphabet], genotype_conf)
    # Morphology moving commands
    elif symbol_category == 3:
        alphabet = random.randint(0, len(Alphabet.morphology_moving_commands()) - 1)
        symbol = Plasticoding.build_symbol(Alphabet.morphology_moving_commands()[alphabet], genotype_conf)
    # Controller moving commands
    elif symbol_category == 4:
        alphabet = random.randint(0, len(Alphabet.controller_moving_commands()) - 1)
        symbol = Plasticoding.build_symbol(Alphabet.controller_moving_commands()[alphabet], genotype_conf)
    # Controller changing commands
    elif symbol_category == 5:
        alphabet = random.randint(0, len(Alphabet.controller_changing_commands()) - 1)
        symbol = Plasticoding.build_symbol(Alphabet.controller_changing_commands()[alphabet], genotype_conf)
    else:
        raise Exception(
            'random number did not generate a number between 1 and 5. The value was: {}'.format(symbol_category))

    return symbol


def handle_addition(genotype, genotype_conf):
    """
    Adds symbol to genotype

    :param genotype: genotype to add to
    :param genotype_conf: configuration for the genotype

    :return: genotype
    """

    target_letter = random.choice(list(genotype.grammar))
    target_clause = random.choice(range(0, len(genotype.grammar[target_letter])))

    if target_letter == Alphabet.CORE_COMPONENT:
        addition_index = random.randint(1, len(genotype.grammar[target_letter][target_clause][1]) - 1)
    else:
        addition_index = random.randint(0, len(genotype.grammar[target_letter][target_clause][1]) - 1)
    symbol_to_add = generate_symbol(genotype_conf)
    genotype.grammar[target_letter][target_clause][1].insert(addition_index, symbol_to_add)

    genotype_logger.info(
        f'mutation: add {symbol_to_add} in {genotype.id} for {target_letter} in {target_clause} at {addition_index}.')
    return genotype


def handle_clause(genotype, mutation_conf):


    max_terms_clause = mutation_conf.genotype_conf.max_terms_clause

    target_letter = random.choice(list(genotype.grammar))
    target_clause = random.choice(range(0, len(genotype.grammar[target_letter])))

    environmental_conditions = mutation_conf.genotype_conf.environmental_conditions
    logic_operators = mutation_conf.genotype_conf.logic_operators

    # defines which mutations are possible

    possible_mutations = ['flipping_value']

    if len(genotype.grammar[target_letter][target_clause][0]) > 1:
        possible_mutations.append('deletion')
        possible_mutations.append('flipping_operator')

    if len(genotype.grammar[target_letter][target_clause][0]) < max_terms_clause:
        possible_mutations.append('addition')

    mutation_type = random.choice(possible_mutations)

    # deletes terms items and logic operator
    if mutation_type == 'deletion':
        position_delete = random.choice(range(0, len(genotype.grammar[target_letter][target_clause][0]) + 1, 2))
        genotype.grammar[target_letter][target_clause][0].pop(position_delete)
        if position_delete == 0:
            genotype.grammar[target_letter][target_clause][0].pop(position_delete)
        else:
            genotype.grammar[target_letter][target_clause][0].pop(position_delete-1)

    if mutation_type == 'addition':

        term = random.choice(environmental_conditions)
        state = random.choice([True, False])

        genotype.grammar[target_letter][target_clause][0].append([random.choice(logic_operators)])
        genotype.grammar[target_letter][target_clause][0].append([term,  '==', state])

    if mutation_type == 'flipping_value':
        position_flip = random.choice(range(0, len(genotype.grammar[target_letter][target_clause][0]) + 1, 2))
        if genotype.grammar[target_letter][target_clause][0][position_flip][2]:
            genotype.grammar[target_letter][target_clause][0][position_flip][2] = False
        else:
            genotype.grammar[target_letter][target_clause][0][position_flip][2] = True

    if mutation_type == 'flipping_operator':
        position_flip = random.choice(range(1, len(genotype.grammar[target_letter][target_clause][0]), 2))
        if genotype.grammar[target_letter][target_clause][0][position_flip][0] == 'and':
            genotype.grammar[target_letter][target_clause][0][position_flip][0] = 'or'
        else:
            genotype.grammar[target_letter][target_clause][0][position_flip][0] = 'and'

    return genotype

def standard_mutation(genotype, mutation_conf):
    """
    Mutates genotype through addition/removal/swapping of symbols

    :param genotype: genotype to be mutated
    :param mutation_conf: configuration for mutation

    :return: modified genotype
    """
    new_genotype = genotype.clone()
    mutation_attempt = random.uniform(0.0, 1.0)
    if mutation_attempt > mutation_conf.mutation_prob:
        return new_genotype
    else:
        if mutation_conf.genotype_conf.plastic:
            mutation_type = random.randint(1, 4)  # NTS: better way?
        else:
            mutation_type = random.randint(1, 3)

        if mutation_type == 1:
            modified_genotype = handle_deletion(new_genotype)
        elif mutation_type == 2:
            modified_genotype = handle_swap(new_genotype)
        elif mutation_type == 3:
            modified_genotype = handle_addition(new_genotype, mutation_conf.genotype_conf)
        elif mutation_type == 4:
            modified_genotype = handle_clause(new_genotype, mutation_conf)
        else:
            raise Exception(
                'mutation_type value was not in the expected range (1,3). The value was: {}'.format(mutation_type))
        return modified_genotype
