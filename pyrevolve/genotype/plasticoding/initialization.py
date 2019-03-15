from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet
import random

def random_initialization(conf):
    """
    Initializing the ...
    :param conf: e_max_groups, maximum number of groups of symbols
    :return: a random new Genome
    :rtype: Plasticoding
    """
    s_segments = random.randint(1, conf.e_max_groups)
    grammar = {}

    for symbol in Alphabet.modules():

        if symbol[0] == Alphabet.CORE_COMPONENT:
            grammar[symbol[0]] = [[Alphabet.CORE_COMPONENT, []]]
        else:
            grammar[symbol[0]] = []

        for s in range(0, s_segments):

            symbol_module = random.randint(
                                        1, len(Alphabet.modules()) - 1)
            symbol_mounting = random.randint(
                                        0, len(Alphabet.morphologyMountingCommands()) - 1)
            symbol_morph_moving = random.randint(
                                        0, len(Alphabet.morphologyMovingCommands()) - 1)
            symbol_contr_moving = random.randint(
                                        0, len(Alphabet.controllerMovingCommands()) - 1)
            symbol_changing = random.randint(
                                        0, len(Alphabet.controllerChangingCommands()) - 1)

            grammar[symbol[0]].extend([
                                   Plasticoding.build_symbol(
                                       Alphabet.controllerMovingCommands()[symbol_contr_moving], conf),
                                   Plasticoding.build_symbol(
                                       Alphabet.controllerChangingCommands()[symbol_changing], conf),
                                   Plasticoding.build_symbol(
                                       Alphabet.morphologyMountingCommands()[symbol_mounting], conf),
                                   Plasticoding.build_symbol(
                                       Alphabet.modules()[symbol_module], conf),
                                   Plasticoding.build_symbol(
                                       Alphabet.morphologyMovingCommands()[symbol_morph_moving], conf),
                                  ])
    return grammar

