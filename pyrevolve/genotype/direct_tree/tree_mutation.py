import math
import random
from typing import Callable, List, Any, Optional, Iterable, Tuple

from pyrevolve.genotype.direct_tree.direct_tree_utils import subtree_size, recursive_iterate_modules, duplicate_subtree
from pyrevolve.genotype.direct_tree.compound_mutation import DirectTreeNEATMutationConfig
from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeMutationConfig, DirectTreeGenotypeConfig
from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeNEATGenotype
from pyrevolve.util import decide
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.revolve_module import CoreModule, RevolveModule, Orientation


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
        delete_random_subtree(tree, genotype_conf)

    # duplicate random subtree
    if decide(genotype_conf.mutation.p_duplicate_subtree):
        duplicate_random_subtree(tree, genotype_conf)

    # swap random subtree
    if decide(genotype_conf.mutation.p_swap_subtree):
        pass  # TODO

    # mutate oscillators
    if decide(genotype_conf.mutation.p_mutate_oscillators):
        pass  # TODO

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
    for parent, module, depth in recursive_iterate_modules(root):
        _subtree_size = subtree_size(module)
        if parent is None:
            continue
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


def duplicate_random_subtree(root: RevolveModule, conf: DirectTreeGenotypeConfig) -> None:
    """
    Picks a random subtree that can be duplicated within the robot
    boundaries, copies it and attaches it to a random free slot.
    :param root: root of the robot tree
    :param conf: direct tree genotype configuration
    """
    robotsize = subtree_size(root)
    max_add_size = conf.max_parts - robotsize

    # Create a list of subtrees that is not larger than max_add_size
    module_list: List[Tuple[RevolveModule, RevolveModule, int]] = []
    empty_slot_list: List[Tuple[RevolveModule, int]] = []
    for parent, module, depth in recursive_iterate_modules(root):
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
        return
    if not empty_slot_list:
        return

    # choose random tree to duplicate
    parent, subtree_root, _subtree_size = random.choice(module_list)
    # choose random empty slot to where the duplication is created
    target_parent, target_empty_slot = random.choice(empty_slot_list)

    # deep copy the source subtree
    subtree_root = duplicate_subtree(subtree_root)
    # and attach it
    target_parent.children[target_empty_slot] = subtree_root
