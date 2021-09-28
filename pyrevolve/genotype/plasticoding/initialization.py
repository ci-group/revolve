from __future__ import annotations
import random
from pyrevolve.genotype.plasticoding.plasticoding import Alphabet
from pyrevolve.genotype.plasticoding.plasticoding import Plasticoding

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Dict, List
    from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig


def _generate_random_grammar(conf: PlasticodingConfig) -> Dict[Alphabet, List]:
    """
    Initializing a new genotype,
    :param conf: e_max_groups, maximum number of groups of symbols
    :return: a random new Genome
    """
    s_segments = random.randint(1, conf.e_max_groups)
    grammar = {}

    for symbol in Alphabet.wordify(Alphabet.modules(conf.allow_vertical_brick, conf.allow_linear_joint)):

        if symbol[0] == conf.axiom_w:
            grammar[symbol[0]] = [[conf.axiom_w, []]]
        else:
            grammar[symbol[0]] = []

        for s in range(0, s_segments):
            symbol_module = random.randint(
                1, len(Alphabet.modules(conf.allow_vertical_brick, conf.allow_linear_joint)) - 1)
            symbol_mounting = random.randint(
                0, len(Alphabet.morphology_mounting_commands()) - 1)
            symbol_morph_moving = random.randint(
                0, len(Alphabet.morphology_moving_commands(conf.use_movement_commands,
                                                           conf.use_rotation_commands,
                                                           conf.use_movement_stack)) - 1)
            symbol_contr_moving = random.randint(
                0, len(Alphabet.controller_moving_commands()) - 1)
            symbol_changing = random.randint(
                0, len(Alphabet.controller_changing_commands()) - 1)

            grammar[symbol[0]].extend([
                Plasticoding.build_symbol(
                    Alphabet.wordify(Alphabet.controller_moving_commands())[symbol_contr_moving], conf),
                Plasticoding.build_symbol(
                    Alphabet.wordify(Alphabet.controller_changing_commands())[symbol_changing], conf),
                Plasticoding.build_symbol(
                    Alphabet.wordify(Alphabet.morphology_mounting_commands())[symbol_mounting], conf),
                Plasticoding.build_symbol(
                    Alphabet.wordify(Alphabet.modules(conf.allow_vertical_brick, conf.allow_linear_joint))[symbol_module], conf),
                Plasticoding.build_symbol(
                    Alphabet.wordify(Alphabet.morphology_moving_commands(
                        conf.use_movement_commands, conf.use_rotation_commands, conf.use_movement_stack)
                    )[symbol_morph_moving], conf),
            ])
    return grammar


def random_initialization(conf: PlasticodingConfig, _id: int) -> Plasticoding:
    """
    Initializing a random genotype.
    :param conf: Plasticoding genotype configuration
    :param _id: id of the newly created genotype
    :return: a Plasticoding Genome
    """
    genotype = Plasticoding(conf, _id)
    genotype.grammar = _generate_random_grammar(conf)
    return genotype
