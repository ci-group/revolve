from __future__ import absolute_import

from ... import TreeGenerator, Tree


class RobogenTreeGenerator(TreeGenerator):
    """
    Tree generator with some additions.
    """

    def __init__(self, body_gen, brain_gen, conf):
        """
        :return:
        """
        self.conf = conf
        super(RobogenTreeGenerator, self).__init__(body_gen, brain_gen)

    def generate_tree(self) -> Tree:
        """
        Overrides `generate_tree` to force robot planarity. Robots
        without output neurons are also discarded because we can be
        certain they will not be able to move.
        :return:
        """
        outputs = -1
        tree = None
        while outputs <= 0:
            tree = super(RobogenTreeGenerator, self).generate_tree()
            _, outputs, _ = tree.root.io_count(recursive=True)

        if self.conf.enforce_planarity:
            make_planar(tree.root)

        return tree


def make_planar(node, current_orientation=0):
    """
    Takes a generated tree and enforces planarity. This uses
    the convenient fact that all current body part slots
    lie in a plane, so we only have to fix it so that
    bricks and parametric bar joints have an overall zero
    orientation.

    :param node:
    :type node: Node
    :param current_orientation: Method is called recursively, using this
                                as the traversing orientation.
    :return:
    """
    if node.is_root():
        node.part.orientation = 0
    elif node.part.type in ("FixedBrick", "ParametricBarJoint"):
        node.part.orientation = (360 - current_orientation) % 360

    for conn in node.child_connections():
        make_planar(
                conn.node,
                (current_orientation + node.part.orientation) % 360)
