import random
import sys
from typing import List, Tuple

from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeGenotypeConfig
from pyrevolve.genotype.direct_tree.direct_tree_utils import recursive_iterate_modules, subtree_size, duplicate_subtree
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype
from pyrevolve.revolve_bot import RevolveModule


def crossover(parent_a: DirectTreeGenotype,
              parent_b: DirectTreeGenotype,
              conf: DirectTreeGenotypeConfig,
              new_id: int) \
        -> DirectTreeGenotype:
    """
    Performs actual crossover between two robot trees, parent_a and parent_b. This
    works as follows:
    - Robot `a` is copied
    - A random node `q` is picked from this copied robot. This may
      be anything but the root node.
    - We generate a list of nodes from robot b which, when replacing `q`,
      would not violate the robot's specifications. If this list is empty,
      crossover is not performed.
    - We pick a random node `r` from this list
    :return: New genotype
    """
    parent_a_size = subtree_size(parent_a.representation)
    child = parent_a.clone()
    module_list_a: List[Tuple[RevolveModule, int, RevolveModule]] = []
    for module_parent, module_parent_slot, module, depth in recursive_iterate_modules(child.representation):
        if module_parent is None:
            continue
        module_list_a.append((module_parent, module_parent_slot, module))

    module_list_b: List[Tuple[RevolveModule, int]] = []
    for module_parent, _, module, _ in recursive_iterate_modules(parent_b.representation):
        if module_parent is None:
            continue
        module_size = subtree_size(module)
        module_list_b.append((module, module_size))

    crossover_point_found = False
    n_tries = 100
    while not crossover_point_found and n_tries > 0:
        n_tries -= 1
        module_parent_a, module_parent_a_slot, module_a = random.choice(module_list_a)
        module_a_size = subtree_size(module_a)

        def compatible(module_b: RevolveModule, module_b_size: int) -> bool:
            new_size = parent_a_size - module_a_size + module_b_size
            return conf.min_parts <= new_size <= conf.max_parts

        unrelated_module_list = [e for e in module_list_b if compatible(*e)]
        if not unrelated_module_list:
            continue

        module_b, _ = random.choice(unrelated_module_list)

        module_parent_a.children[module_parent_a_slot] = duplicate_subtree(module_b)
        crossover_point_found = True

    if not crossover_point_found:
        print(f'Crossover between genomes {parent_a.id} and {parent_b.id} was not successful after 100 trials,'
              f' returning a clone of {parent_a.id} unchanged', file=sys.stderr)

    child.id = new_id
    return child
