import random

from pyrevolve.angle import Tree
from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype
from pyrevolve.genotype.direct_tree.tree_helper import _renumber, _node_list


class DirectTreeCrossoverConfig():

    def __init__(self):
        pass


class Crossover(object):
    """
    Crossover class. Its working part is the `crossover` function, see
    there for a detailed description.
    """
    def __init__(self, robogen_tree_generator: RobogenTreeGenerator):
        """
        Although the crossover class does not perform parameter mutations, robot
        limits are still required knowledge for crossover choices. It is because
        of this the body / brain generators are passed here.

        :return:
        """
        self.robogen_tree_generator: RobogenTreeGenerator = robogen_tree_generator

    def crossover(self, parents, genotype_conf, crossover_conf):
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

        :return:
        :rtype: tuple(bool, Tree)
        """
        a = parents[0].genotype.representation
        b = parents[1].genotype.representation
        print(a.__class__, b.__class__)
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
        max_parts = self.robogen_tree_generator.body_gen.max_parts
        max_inputs = self.robogen_tree_generator.body_gen.max_inputs
        max_outputs = self.robogen_tree_generator.body_gen.max_outputs
        max_hidden = self.robogen_tree_generator.brain_gen.max_hidden

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
            genotype = DirectTreeGenotype(genotype_conf, None)
            genotype.root = result
            return genotype.clone()

        # Pick `r` from list.
        r = random.choice(replace_nodes)

        # Replace the subtree starting at `q` with `r`
        # Determine the connection slots. Slots are always relative to
        # the node defining the connection. We thus need the `to_slot`
        # of the parent connection of the original node, and connect it
        # to the `from_slot` on the new node.
        conn = q.parent_connection()
        start_node = conn.node
        from_slot = conn.to_slot
        to_slot = r.parent_connection().from_slot

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
        # Note that we have already correctly renumbered both the root tree
        # and the child above.
        start_node.set_connection(from_slot, to_slot, r, parent=True)

        genome = DirectTreeGenotype(genotype_conf, None)
        genome.representation = Tree(result)
        print("results ", result)
        return genome.clone()
