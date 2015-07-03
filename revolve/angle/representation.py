from ..spec.msgs import Robot, BodyPart, Neuron


def _process_body_part(part, node, brain):
    """
    :param part:
    :type part: BodyPart
    :param node:
    :type node: Node
    :param brain:
    :type brain: NeuralNetwork
    :return:
    """
    part.CopyFrom(node.part)

    # Process neurons
    counters = {"input": 0, "output": 0, "hidden": 0}
    for neuron in node.neurons:
        nw = brain.neuron.add()
        nw.CopyFrom(neuron)
        nw.part_id = part.id
        nw.id = node.get_neuron_id(neuron.layer, counters[nw.layer])
        counters[nw.layer] += 1

    # Process neuron connections
    for src, dst, weight in node.get_neural_connections():
        conn = brain.connection.add()
        conn.src = src
        conn.dst = dst
        conn.weight = weight

    # Process children
    for from_slot, (to_slot, child, _) in node.parent_connections():

        conn = part.child.add()
        conn.src = from_slot
        conn.dst = to_slot
        _process_body_part(conn.part, child, brain)

class Tree(object):
    """
    A tree to represent a robot that can be used for evolution.
    """

    def __init__(self, root):
        """
        :return:
        """
        super(Tree, self).__init__()
        self.root = root

        # Maps node IDs to nodes for looked up nodes
        self._nodes = {}

    def to_robot(self, robot_id=0):
        """
        Turns this tree representation into a protobuf robot.
        """
        robot = Robot()
        robot.id = robot_id
        _process_body_part(robot.body.root, self.root, robot.brain)
        return robot

    def get_node(self, node_id):
        """
        Returns the node with the given ID from this
        tree.

        :param node_id:
        :type node_id: str
        :return:
        :rtype: Node
        """
        if node_id in self._nodes:
            return self._nodes[node_id]

        return self._get_node(node_id, self.root)

    def _get_node(self, node_id, current):
        """
        Recursion helper for get_node.
        """
        if current.id == node_id:
            return current

        for conn in current.parent_connections():
            self._nodes[conn.node.id] = conn.node
            node = self._get_node(node_id, conn.node)
            if node:
                return node

        return None

    def __len__(self):
        """
        Counts the total number of nodes in the tree
        """
        return len(self.root)

class Node(object):
    """
    Single body part node, stores the body part as well as neural
    network information for evolution.
    """

    def __init__(self, part, neurons, body_spec):
        """
        :param part:
        :type part: BodyPart
        :param neurons: List of `Neuron` objects. Only types and params are relevant,
                        IDs are overwritten when a robot object is generated.
        :type neurons: list[Neuron]
        :return:
        """
        super(Node, self).__init__()

        # Copy the node ID as the part ID
        self.id = part.id
        self.spec = body_spec.get(part.type)

        # Copy the given body part without the connections
        self.part = BodyPart()
        self.part.id = part.id
        self.part.type = part.type
        self.part.orientation = part.orientation
        for param in part.param:
            new_param = self.part.param.add()
            new_param.CopyFrom(param)

        # Maps slot ids to other nodes
        self.connections = {}

        # Neural net connection paths plus weights
        self.neural_connections = []

        # Neurons specified for this node
        self.neurons = neurons
        self.num_hidden = len([n for n in neurons if n.type == "hidden"])

        # Check if given number of inputs / outputs matches spec
        inputs = len([n for n in neurons if n.type == "input"])
        outputs = len([n for n in neurons if n.type == "output"])
        if inputs != self.spec.inputs or outputs != self.spec.outputs:
            raise Exception("Part input / output mismatch.")

    def add_connection(self, from_slot, to_slot, node, parent=True):
        """
        Adds a bidirectional node body connection.
        """
        self.connections[from_slot] = BodyConnection(from_slot, to_slot, node, parent)
        if parent:
            node.add_connection(to_slot, from_slot, self, parent=False)

    def get_target(self, path):
        """
        Returns the node that is located at the given path following
        slots starting at the current node, or None if that node doesn't
        exist.
        """
        if not path:
            return self

        slot = path[0]
        other = self.connections.get(slot, None)
        return other.get_target(path[1:]) if other else None

    def get_path(self, target, origin=None):
        """
        Tries to find the path to the given target
        node. If an origin node is given, paths to
        that node are not followed.
        :param target:
        :type target: Node
        :param origin:
        :type origin: Node
        :return: list|bool
        """
        for conn in self.connections.values():
            if conn.node is origin:
                continue

            if conn.node is target:
                return [conn.from_slot]

            path = conn.node.get_path(target, self)
            if path:
                return [conn.from_slot] + path

        return False

    def has_neuron(self, neuron_type, offset):
        """
        :param neuron_type: "input", "hidden" or "output"
        :param offset: Index of the neuron
        :type offset: int
        :type neuron_type: str
        """
        if neuron_type == "hidden":
            return offset < self.num_hidden
        elif neuron_type == "input":
            return offset < self.spec.inputs
        else:
            return offset < self.spec.outputs

    def get_neuron_id(self, neuron_type, offset):
        """
        Convenience function to return the id corresponding to
        a neuron of a given type / offset. Note that this
        does not use the IDs of the current neurons, but rather
        returns the neuron ID as it will be after the robot
        has been generated.
        """
        t = {"input": "in", "output": "out", "hidden": "hidden"}[neuron_type]
        return "%s-%s-%d" % (self.part.id, t, offset)

    def get_neuron_offset(self, neuron):
        """
        Returns the type offset of the given neuron.
        :param neuron:
        :type neuron: Neuron
        :return:
        """
        offset = 0
        for other in self.neurons:
            if other is neuron:
                return offset

            if other.type == neuron.type:
                offset += 1

        return False

    def get_neural_connections(self):
        """
        Attempts to traverse neural connections and returns list
        of the ones that are valid.
        """
        results = []
        taken = set()
        for conn in self.neural_connections:
            src_type, src_idx = conn.src
            if not self.has_neuron(src_type, src_idx):
                continue

            target = self.get_target(conn.path)
            if not target:
                continue

            dst_type, dst_idx = conn.dst
            if not target.has_neuron(dst_type, dst_idx):
                continue

            # Connection is possible
            src_id = self.get_neuron_id(src_type, src_idx)
            dst_id = target.get_neuron_id(dst_type, dst_idx)

            # Ignore duplicates
            # Duplicates could happen because paths aren't unique - it's possible to
            # go back and forth between two nodes.
            pair = (src_id, dst_id)
            if pair in taken:
                continue

            taken.add(pair)
            results.append((src_id, dst_id, conn.weight))

        return results

    def parent_connections(self):
        """
        Returns a generator for connections for which
        this node is the parent.
        """
        for v in self.connections.values():
            if not v.parent:
                continue

            yield v

    def is_root(self):
        """
        Returns true if this node has no non-parent connections
        :return:
        """
        for v in self.connections.values():
            if v.parent:
                return False

        return True

    def __len__(self):
        """
        Returns the total number of nodes in the subtree for which
        this node is the root.

        :rtype: int
        :return: Subtree size
        """
        return sum(len(v.node) for v in self.parent_connections()) + 1

    def add_neural_connection(self, src, dst, dst_part, weight):
        """
        :param src:
        :type src: Neuron
        :param dst:
        :type dst: Neuron
        :param dst_part:
        :type dst_part: Node
        :param weight:
        """
        path = self.get_path(dst_part)
        src_offset = self.get_neuron_offset(src)
        dst_offset = dst_part.get_neuron_offset(dst)
        self.neural_connections.append(NeuralConnection(
            (src.type, src_offset),
            (dst.type, dst_offset),
            path,
            weight
        ))


class BodyConnection(object):
    """
    Body connection
    """
    def __init__(self, from_slot, to_slot, node, parent):
        """

        :param from_slot:
        :param to_slot:
        :param node:
        :param parent:
        """
        self.parent = parent
        self.node = node
        self.to_slot = to_slot
        self.from_slot = from_slot


class NeuralConnection(object):
    """
    Brain connection
    """

    def __init__(self, src, dst, path, weight):
        """
        :param src: type, index tuple
        :param dst: type, index tuple
        :param weight: Connection weight
        :param path: An iterable of slots to follow. This path
                     needs to be followed from the source node
                     to find the target neuron. This target
                     neuron might not exist.
        :return:
        """
        super(NeuralConnection, self).__init__()
        self.src = src
        self.dst = dst
        self.weight = weight
        self.path = tuple(path)
