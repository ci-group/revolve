"""
Includes functions for robot tree analysis, to:

- Determine the number of extremities per robot
- Determine the number of joints per robot
-
"""
from __future__ import absolute_import

import itertools


def count_extremities(node):
    """
    Counts the extremities in the subtree represented by the given node.
    :type node: Node
    """
    # Count all leaf nodes to get the extremities
    if node.is_leaf():
        return 1
    else:
        return len([c for c in node.get_children()
                    if not len(list(c.child_connections()))])


def count_types(node, types):
    """
    :type node: Node
    :param node:
    :type types: tuple
    """
    base = 1 if node.part.type in types else 0
    return base + len([c for c in node.get_children() if c.part.type in types])


def count_joints(node):
    return count_types(node, ("ActiveHinge", "Hinge"))


def count_motors(node):
    return count_types(node, ("ActiveHinge",))


def list_extremities(node):
    """
    Returns an iterator with the first node of each
    extremity in the subtree represented by the given node.
    """
    # If the list of extremities on this node is 1, return this node
    if count_extremities(node) == 1:
        return [node]

    # Otherwise return the starting point for all extremities on child nodes
    return list(itertools.chain(*(list_extremities(c.node)
                                  for c in node.child_connections())))


def joints_per_extremity(node):
    """
    Returns a list with the number of joints encountered in each extremity
    in the subtree represented by the given node.
    :type node: Node
    """
    return [count_extremities(c) for c in list_extremities(node)]


def count_connections(node):
    """
    :type node: Node
    """
    return len(node.get_neural_connections()) + \
           sum(count_connections(c.node) for c in node.child_connections())
