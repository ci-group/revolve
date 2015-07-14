import random
from .representation import Tree, Node
from ..generate import BodyGenerator, NeuralNetworkGenerator


def decide(probability):
    """
    Returns True with the given probability
    :param probability:
    :return:
    """
    return random.random() < probability


def _node_list(node, root=True):
    """
    Recursively builds a linear node list
    from a root node.

    :param node:
    :type node: Node
    :param root: Include the given node or not
    :return:
    """
    if root:
        lst = [node]
    else:
        lst = []

    for conn in node.parent_connections():
        lst += _node_list(conn.node, root=True)

    return lst


def _renumber(node, base=0):
    """
    :param base:
    :param node:
    :return:
    """
    for node in _node_list(node):
        node.id = "node-%d" % base
        base += 1

    return base


class Crossover(object):
    """
    Crossover class. Its working part is the `crossover` function, see
    there for a detailed description.
    """
    def __init__(self, body_gen, brain_gen):
        """
        Although the crossover class does not perform parameter mutations, robot
        limits are still required knowledge for crossover choices. It is because
        of this the body / brain generators are passed here.

        :param body_gen: A body generator for this robot spec.
        :type body_gen: BodyGenerator
        :param brain_gen: A neural net generator for this robot spec.
        :type brain_gen: NeuralNetworkGenerator
        :return:
        """
        self.brain_gen = brain_gen
        self.body_gen = body_gen

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
        :rtype: Tree
        """
        result = a.root.copy()

        # All nodes except the root node
        crossover_points = _node_list(result)[1:]
        q = random.choice(crossover_points)

        # Create list of valid crossover points from `b`
        # Get the total list of nodes excluding the root
        b_nodes = _node_list(b.root, root=False)

        # Determine the current robot statistics, subtracting
        # everything after the crossover point.
        inputs, outputs, hidden = result.io_count()
        num_nodes = len(result)

        c_i, c_o, c_h = q.io_count()
        inputs -= c_i
        outputs -= c_o
        hidden -= c_h
        num_nodes -= len(q)

        replace_nodes = []
        max_parts = self.body_gen.max_parts
        max_inputs = self.body_gen.max_inputs
        max_outputs = self.body_gen.max_outputs
        max_hidden = self.brain_gen.max_hidden

        for node in b_nodes:
            n_nodes = len(node)
            if num_nodes + n_nodes > max_parts:
                # Using this node would result in too many parts
                continue

            n_i, n_o, n_h = node.io_count()
            t_i, t_o, t_h = n_i + inputs, n_o + outputs, n_h + hidden
            if t_i > max_inputs or t_o > max_outputs or t_h > max_hidden:
                continue

            replace_nodes.append(node)

        if not replace_nodes:
            # No possible replacement nodes - no crossover
            return False, Tree(result)

        # Pick `r` from list.
        r = random.choice(replace_nodes)

        # Replace the subtree starting at `q` with `r`
        # Determine the connection slots. Slots are always relative to
        # the node defining the connection. We thus need the `to_slot`
        # of the parent connection of the original node, and connect it
        # to the `from_slot` on the new node.
        conn = q.child_connection()
        start_node = conn.node
        from_slot = conn.to_slot
        to_slot = r.child_connection().from_slot

        # Remove the existing connection. `set_connection` will also do this,
        # but this way we make sure the trees never contain duplicate IDs
        # and that seems desireable somehow.
        start_node.remove_connection(from_slot)

        # We don't want to modify `b`, so copy `r` without parent
        r = r.copy(copy_parent=False)

        # Update node IDs, duplicates are quite likely at this point
        base = _renumber(result)
        _renumber(r, base)

        # Set the actual connection and return the tree
        result.set_connection(from_slot, to_slot, r, parent=True)

        return True, Tree(result)


class Mutator(object):
    """
    Parameter mutation class. Mutation is achieved by generating
    a new value for each parameter and combining it with the
    old parameter in the ratio specified by the parameter's
    epsilon value.
    """

    def __init__(self, body_gen, brain_gen,
                 p_remove_hidden_neuron=0.05,
                 p_remove_brain_connection=0.05,
                 p_delete_subtree=0.05,
                 p_swap_subtree=0.05):
        """
        :param body_gen: A body generator for this robot.
        :type body_gen: BodyGenerator
        :param brain_gen: A neural net generator for this robot
        :type brain_gen: NeuralNetworkGenerator
        :return:
        """
        self.p_swap_subtree = p_swap_subtree
        self.p_delete_subtree = p_delete_subtree
        self.p_remove_brain_connection = p_remove_brain_connection
        self.p_remove_hidden_neuron = p_remove_hidden_neuron
        self.brain_gen = brain_gen
        self.body_gen = body_gen

    def mutate(self, tree, in_place=True):
        """
        Mutates the robot tree. This performs the following operations:

        - Body parameters are mutated
        - Brain parameters are mutated
        - A subtree might be removed
        - A subtree might be duplicated
        - Two subtrees might be swapped
        - Subtrees are duplicated at random
        - Body parts are added at random

        :param tree:
        :type tree: Tree
        :param in_place:
        :return:
        """
        root = tree.root if in_place else tree.root.copy()

        # We first perform all destructive operations, then
        # all modifying operations, and finally all additive operations
        self.delete_random_subtree(root)
        self.swap_random_subtrees(root)

        for node in _node_list(root, root=True):
            # Remove neurons / connections at random
            # TODO Delete hidden neurons
            # TODO Delete brain connections

            # Mutate body and brain parameters
            self.mutate_node_body_parameters(node)
            self.mutate_node_brain_parameters(node)

        # Next, we perform additive changes to the body
        self.add_random_body_part(root)

        # We then add new hidden neurons
        # TODO Select a new number of hidden neurons and add them

    def delete_random_subtree(self, root):
        """
        :param root: Root node of the tree
        :return: Whether or not a subtree was removed
        :rtype: bool
        """
        node_list = _node_list(root, root=False)
        if not decide(self.p_delete_subtree):
            return False

        max_remove_size = len(node_list) - self.body_gen.min_parts
        items = [node for node in node_list if len(node) <= max_remove_size]
        if not items:
            return False

        subtree = random.choice(items)
        self.remove_subtree(subtree)

    def swap_random_subtrees(self, root):
        """

        :param root:
        :return:
        """
        raise NotImplementedError("TODO Implement")

    def add_random_body_part(self, root):
        """

        :param root:
        :return:
        """
        raise NotImplementedError("TODO Implement")

    def mutate_node_body_parameters(self, node):
        """
        Mutate a single node's body parameters.
        This generates a new random set of parameters for the node, and
        changes the value of each parameter to

        `(1 - e) * old_value + e * new_value`

        Here `e` is the epsilon value defined in the parameter spec, which
        gives an upper bound for the percentual change in parameter value.
        :param node:
        :return:
        """
        spec = self.body_gen.spec.get(node.part.type)
        nw_params = spec.get_epsilon_mutated_parameters(node.part.param, serialize=False)
        spec.set_parameters(node.part.param, nw_params)

    def mutate_node_brain_parameters(self, node):
        """
        :param node:
        :type node: Node
        :return:
        """
        for neuron in node.neurons:
            spec = self.brain_gen.spec.get(neuron.type)
            nw_params = spec.get_epsilon_mutated_parameters(neuron.param, serialize=False)
            spec.set_parameters(neuron.param, nw_params)

    def remove_subtree(self, node):
        """
        Removes the subtree starting from the given node
        :param node:
        :type node: Node
        :return:
        """
        conn = node.child_connection()
        node.remove_connection(conn.from_slot)
