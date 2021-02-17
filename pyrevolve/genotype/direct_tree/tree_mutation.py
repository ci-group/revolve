import math
import random
from typing import Callable, List, Any, Optional, Iterable, Tuple, Union

from pyrevolve.genotype.direct_tree.direct_tree_utils import subtree_size, recursive_iterate_modules, duplicate_subtree
from pyrevolve.genotype.direct_tree.compound_mutation import DirectTreeNEATMutationConfig
from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeMutationConfig, DirectTreeGenotypeConfig
from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeNEATGenotype
from pyrevolve.util import decide
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.revolve_module import CoreModule, RevolveModule, Orientation, ActiveHingeModule


def mutate(genotype: DirectTreeGenotype,
           genotype_conf: DirectTreeGenotypeConfig,
           in_place=False):
    """
    Mutates the robot tree. This performs the following operations:
    - Body parameters are mutated
    - Brain parameters are mutated
    - A subtree might be removed
    - A subtree might be duplicated
    - Two subtrees might be swapped
    - Subtrees are duplicated at random
    - Body parts are added at random
    Mutation operations are designed to make changes to the robot
    whilst keeping it at roughly the same complexity. This means that:
    - The probability of a new body part being added is proportional
      to the average number of body parts being removed in a single
      step.
    - The number of newly created hidden neurons and neural connections
      equals the average number of neurons and connections removed in
      each step.
    :param genotype:
    :param genotype_conf:
    :param in_place:
    :return: mutated version of the genome
    """
    if not in_place:
        genotype = genotype.clone()
    tree: CoreModule = genotype.representation

    revolvebot = RevolveBot(genotype.id)
    revolvebot._body = tree

    # delete_random_subtree
    if decide(genotype_conf.mutation.p_delete_subtree):
        r, n = delete_random_subtree(tree, genotype_conf)
        if r is not None:
            print(f"DELETED {n} ELEMENTS")

    # TODO generate random subtree

    # TODO random rotate modules

    # duplicate random subtree
    if decide(genotype_conf.mutation.p_duplicate_subtree):
        if duplicate_random_subtree(tree, genotype_conf):
            print("DUPLICATED")

    # swap random subtree
    if decide(genotype_conf.mutation.p_swap_subtree):
        if swap_random_subtree(tree):
            print("SWAPPED")

    # mutate oscillators
    if decide(genotype_conf.mutation.p_mutate_oscillators):
        mutate_oscillators(tree, genotype_conf)

    return genotype


def delete_random_subtree(root: RevolveModule,
                          genotype_conf: DirectTreeGenotypeConfig) \
        -> (Optional[RevolveModule], int):
    """
    Deletes a subtree at random, assuming this is possible within
    the boundaries of the robot specification.
    :param root: Root node of the tree
    :param genotype_conf:
    :return: The removed subtree (or None if no subtree was removed) and the size of the subtree (the amount of modules removed)
    """
    robot_size = subtree_size(root)
    max_remove_list = robot_size - genotype_conf.min_parts

    module_list = []
    for parent, parent_slot, module, depth in recursive_iterate_modules(root):
        if parent is None:
            continue
        _subtree_size = subtree_size(module)
        # This line of code above it's slow, because it's recalculated for each subtree.
        # But I don't care at the moment. You can speed it up if you want.
        if _subtree_size > max_remove_list:
            continue
        module_list.append((parent, module, _subtree_size))

    if not module_list:
        return None, 0

    parent, subtree_root, _subtree_size = random.choice(module_list)
    for i, module in parent.iter_children():
        if module == subtree_root:
            parent.children[i] = None
            break
    else:
        # break was not reached, module not found about children
        raise RuntimeError("Subtree not found in the parent module!")
    return subtree_root, _subtree_size


def duplicate_random_subtree(root: RevolveModule, conf: DirectTreeGenotypeConfig) -> bool:
    """
    Picks a random subtree that can be duplicated within the robot
    boundaries, copies it and attaches it to a random free slot.
    :param root: root of the robot tree
    :param conf: direct tree genotype configuration
    :return: True if duplication happened
    """
    robotsize = subtree_size(root)
    max_add_size = conf.max_parts - robotsize

    # Create a list of subtrees that is not larger than max_add_size
    module_list: List[Tuple[RevolveModule, RevolveModule, int]] = []
    empty_slot_list: List[Tuple[RevolveModule, int]] = []
    for parent, parent_slot, module, depth in recursive_iterate_modules(root):
        # Create empty slot list
        for slot, child in module.iter_children():
            # allow back connection only for core block, not others
            _slot = Orientation(slot)
            if _slot is Orientation.BACK and not isinstance(child, CoreModule):
                continue
            if child is None:
                empty_slot_list.append((module, slot))

        if parent is None:
            continue

        _subtree_size = subtree_size(module)
        # This line of code above it's slow, because it's recalculated for each subtree.
        # But I don't care at the moment. You can speed it up if you want.
        if _subtree_size > max_add_size:
            continue
        # Create possible source subtree list
        module_list.append((parent, module, _subtree_size))

    if not module_list:
        return False
    if not empty_slot_list:
        return False

    # choose random tree to duplicate
    parent, subtree_root, _subtree_size = random.choice(module_list)
    # choose random empty slot to where the duplication is created
    target_parent, target_empty_slot = random.choice(empty_slot_list)

    # deep copy the source subtree
    subtree_root = duplicate_subtree(subtree_root)
    # and attach it
    target_parent.children[target_empty_slot] = subtree_root

    return True


def swap_random_subtree(root: RevolveModule) -> bool:
    """
    Picks to random subtrees (which are not parents / children of each
    other) and swaps them.
    :param root: root of the robot tree
    :return: True if swapping happened
    """
    module_list: List[Tuple[RevolveModule, int, RevolveModule]] = []
    for parent, parent_slot, module, depth in recursive_iterate_modules(root):
        if parent is None:
            continue
        module_list.append((parent, parent_slot, module))

    parent_a, parent_a_slot, a = random.choice(module_list)
    a_module_set = set()
    for _, _, module, _ in recursive_iterate_modules(a):
        a_module_set.add(module)

    unrelated_module_list = [e for e in module_list if e[2] not in a_module_set]
    if not unrelated_module_list:
        return False

    parent_b, parent_b_slot, b = random.choice(unrelated_module_list)

    parent_b.children[parent_b_slot] = a
    parent_a.children[parent_a_slot] = b

    return True


def mutate_oscillators(root: RevolveModule, conf: DirectTreeGenotypeConfig) -> None:
    """
    Mutates oscillation
    :param root: root of the robot tree
    :param conf: genotype config for mutation probabilities
    """

    for _, _, module, _ in recursive_iterate_modules(root):
        if isinstance(module, ActiveHingeModule):
            if decide(conf.mutation.p_mutate_oscillator):
                module.oscillator_amplitude += random.gauss(0, conf.mutation.mutate_oscillator_amplitude_sigma)
                module.oscillator_period += random.gauss(0, conf.mutation.mutate_oscillator_period_sigma)
                module.oscillator_phase += random.gauss(0, conf.mutation.mutate_oscillator_phase_sigma)

                # amplitude is clamped between 0 and 1
                module.oscillator_amplitude = clamp(module.oscillator_amplitude, 0, 1)
                # phase and period are periodically repeating every max_oscillation,
                #  so we bound the value between [0,conf.max_oscillation] for convenience
                module.oscillator_phase = module.oscillator_phase % conf.max_oscillation
                module.oscillator_period = module.oscillator_period % conf.max_oscillation


def clamp(value: Union[float, int],
          minvalue: Union[float, int],
          maxvalue: Union[float, int]) \
        -> Union[float, int]:
    """
    Clamps the value to a minimum and maximum
    :param value: source value
    :param minvalue: min possible value
    :param maxvalue: max possible value
    :return: clamped value
    """
    return min(max(minvalue, value), maxvalue)
