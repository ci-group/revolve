from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet
import random
import pprint


def _generate_random_grammar(conf):
    """
    Initializing a new genotype,
    :param conf: e_max_groups, maximum number of groups of symbols
    :return: a random new Genome
    :rtype: dictionary
    """
    s_segments = random.randint(1, conf.e_max_groups)
    grammar = {}

    for symbol in Alphabet.modules():

        if symbol[0] == conf.axiom_w:
            grammar[symbol[0]] = [[conf.axiom_w, []]]
        else:
            grammar[symbol[0]] = []

        for s in range(0, s_segments):
            symbol_module = random.randint(
                1, len(Alphabet.modules()) - 1)
            symbol_mounting = random.randint(
                0, len(Alphabet.morphology_mounting_commands()) - 1)
            symbol_morph_moving = random.randint(
                0, len(Alphabet.morphology_moving_commands()) - 1)
            symbol_contr_moving = random.randint(
                0, len(Alphabet.controller_moving_commands()) - 1)
            symbol_changing = random.randint(
                0, len(Alphabet.controller_changing_commands()) - 1)

            grammar[symbol[0]].extend([
                Plasticoding.build_symbol(
                    Alphabet.controller_moving_commands()[symbol_contr_moving], conf),
                Plasticoding.build_symbol(
                    Alphabet.controller_changing_commands()[symbol_changing], conf),
                Plasticoding.build_symbol(
                    Alphabet.morphology_mounting_commands()[symbol_mounting], conf),
                Plasticoding.build_symbol(
                    Alphabet.modules()[symbol_module], conf),
                Plasticoding.build_symbol(
                    Alphabet.morphology_moving_commands()[symbol_morph_moving], conf),
            ])
    return grammar


def _generate_random_plastic_grammar(conf):
    """
    Initializing a new genotype,
    :param conf: e_max_groups, maximum number of groups of symbols
    :return: a random new Genome
    :rtype: dictionary
    """
    s_segments = random.randint(1, conf.e_max_groups)

    grammar = {}

    for symbol in Alphabet.modules():

        grammar[symbol[0]] = []

        # generates clause and rule for each flavor of the letter
        for flavor in range(0, conf.max_clauses):

            grammar[symbol[0]].append([])

            if symbol[0] == conf.axiom_w:
                grammar[symbol[0]][-1].extend([build_clause(conf.environmental_conditions,
                                                            conf.logic_operators,
                                                            conf.max_terms_clause),
                                               [[conf.axiom_w, []]]])
            else:
                grammar[symbol[0]][-1].extend([build_clause(conf.environmental_conditions,
                                                            conf.logic_operators,
                                                            conf.max_terms_clause),
                                               []])

            for s in range(0, s_segments):

                symbol_module = random.randint(
                    1, len(Alphabet.modules()) - 1)
                symbol_mounting = random.randint(
                    0, len(Alphabet.morphology_mounting_commands()) - 1)
                symbol_morph_moving = random.randint(
                    0, len(Alphabet.morphology_moving_commands()) - 1)
                symbol_contr_moving = random.randint(
                    0, len(Alphabet.controller_moving_commands()) - 1)
                symbol_changing = random.randint(
                    0, len(Alphabet.controller_changing_commands()) - 1)

                grammar[symbol[0]][-1][1].extend([
                    Plasticoding.build_symbol(
                        Alphabet.controller_moving_commands()[symbol_contr_moving], conf),
                    Plasticoding.build_symbol(
                        Alphabet.controller_changing_commands()[symbol_changing], conf),
                    Plasticoding.build_symbol(
                        Alphabet.morphology_mounting_commands()[symbol_mounting], conf),
                    Plasticoding.build_symbol(
                        Alphabet.modules()[symbol_module], conf),
                    Plasticoding.build_symbol(
                        Alphabet.morphology_moving_commands()[symbol_morph_moving], conf),
                ])

    return grammar


def build_clause(environmental_conditions, logic_operators, max_terms_clause):

    clause = []

    num_terms_clause = random.choice(range(1, max_terms_clause+1))
    for term_idx in range(1, num_terms_clause+1):

        # selects a random term and makes a random comparison
        term = random.choice(environmental_conditions)
        state = random.choice([True, False])

        clause.append([term, '==', state])

        # adds logical operators if there are multiple terms
        if term_idx < num_terms_clause:
            clause.append([random.choice(logic_operators)])

    return clause


def random_initialization(conf, next_robot_id):
    """
    Initializing a random genotype.
    :type conf: PlasticodingConfig
    :return: a Genome
    :rtype: Plasticoding
    """
    genotype = Plasticoding(conf, next_robot_id)

    if conf.plastic:
        genotype.grammar = _generate_random_plastic_grammar(conf)
    else:
        genotype.grammar = _generate_random_grammar(conf)
       
    return genotype
