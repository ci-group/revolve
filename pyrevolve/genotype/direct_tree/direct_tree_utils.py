import copy
from collections import deque
from typing import Optional, Iterable, Tuple

from pyrevolve.revolve_bot import RevolveModule


def recursive_iterate_modules(module: RevolveModule,
                              parent: Optional[RevolveModule] = None,
                              parent_slot: Optional[int] = None,
                              depth: int = 1,
                              include_none_child: bool = False) \
        -> Iterable[Tuple[Optional[RevolveModule], Optional[int], RevolveModule, int]]:
    """
    Iterate all modules, depth search first, yielding parent, parent slot, module and depth, starting from root_depth=1.
    Uses recursion.
    :param module: starting module to expand
    :param parent: for internal recursiveness, parent module. leave default
    :param parent_slot: for internal recursiveness, parent module slot. leave default
    :param depth: for internal recursiveness, depth of the module passed in. leave default
    :param include_none_child: if to include also None modules (consider empty as leaves)
    :return: iterator for all modules with (parent, parent_slot, module, depth)
    """
    if module is not None:
        for slot, child in module.iter_children():
            if include_none_child or child is not None:
                for _next in recursive_iterate_modules(child, module, slot, depth+1):
                    yield _next
    yield parent, parent_slot, module, depth


def subtree_size(module: RevolveModule) -> int:
    """
    Calculates the size of the subtree starting from the module
    :param module: root of the subtree
    :return: how many modules the subtree has
    """
    count = 0
    if module is not None:
        for _ in bfs_iterate_modules(root=module):
            count += 1
    return count


def bfs_iterate_modules(root: RevolveModule) \
        -> Iterable[Tuple[Optional[RevolveModule], RevolveModule]]:
    """
    Iterates throw all modules breath first, yielding parent and current module
    :param root: root tree to iterate
    :return: iterator for all modules with respective parent in the form: `(Parent,Module)`
    """
    assert root is not None
    to_process = deque([(None, root)])
    while len(to_process) > 0:
        r: (Optional[RevolveModule], RevolveModule) = to_process.popleft()
        parent, elem = r
        for _i, child in elem.iter_children():
            if child is not None:
                to_process.append((elem, child))
        yield parent, elem


def duplicate_subtree(root: RevolveModule) -> RevolveModule:
    """
    Creates a duplicate of the subtree given as input
    :param root: root of the source subtree
    :return: new duplicated subtree
    """
    assert root is not None
    return copy.deepcopy(root)
