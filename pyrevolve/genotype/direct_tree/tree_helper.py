
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

    for conn in node.child_connections():
        lst += _node_list(conn.node, root=True)

    return lst


def _renumber(node, base=0):
    """
    :param base:
    :param node:
    :type node: Node
    :return:
    """
    for node in _node_list(node):
        node.id = "node-{}".format(base)
        base += 1

    return base


def _delete_subtree(node):
    """
    Removes the subtree starting from the given node
    :param node:
    :type node: Node
    :return:
    """
    conn = node.parent_connection()
    node.remove_connection(conn.from_slot)

