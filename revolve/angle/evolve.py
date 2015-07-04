import random
from .representation import Tree, Node


def _node_list(node):
    """
    Recursively builds a linear node list
    from a root node.

    :param node:
    :type node: Node
    :return:
    """
    lst = [node]
    for conn in node.parent_connections():
        lst += _node_list(conn.node)

    return lst


class Crossover(object):
    """
    Crossover class. It's working part is the `crossover` function.
    """
    def __init__(self, body_spec, brain_spec):
        """
        :return:
        """
        self.brain_spec = brain_spec
        self.body_spec = body_spec

    def crossover(self, a, b):
        """
        Performs actual crossover between two robot trees, a and b. This
        works as follows:

        - Robot `a` is copied
        - A random node `q` is picked from this copied robot. This may
          be anything but the root node.
        - We generate a list of nodes from robot b which, when replacing `q`,
          would not violate the robot's specifications. If this list is empty,
          crossover is not performed.
        - We pick a random node `r` from this list
        :param a:
        :type a: Tree
        :param b:
        :type b: Tree
        :return:
        """
        result = a.root.copy()

        # All nodes except the root node
        crossover_points = _node_list(result)[1:]
        q = random.choice(crossover_points)

        # Create list of valid crossover points from `b`
        # Pick `r` from list
        # Replace the subtree starting at `q` with `r`
        # Update node IDs, duplicates are quite likely
