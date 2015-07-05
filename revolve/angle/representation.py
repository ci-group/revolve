import copy
from ..spec.msgs import Robot, BodyPart, Neuron, NeuralNetwork, Body


def _create_subtree(body_part, brain, body_spec):
    """
    :param body_part:
    :param brain:
    :param body_spec:
    :return:
    """
    # Gather neurons for this part
    neurons = [neuron for neuron in brain.neuron if neuron.partId == body_part.id]
    node = Node(body_part, neurons, body_spec)
    for conn in body_part.child:
        subtree = _create_subtree(conn.part, brain, body_spec)
        node.set_connection(conn.src, conn.dst, subtree)

    return node

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
        nw.partId = part.id
        nw.id = node.get_neuron_id(neuron.layer, counters[nw.layer])
        counters[nw.layer] += 1

    # Process neuron connections
    for src, dst, weight in node.get_neural_connections():
        conn = brain.connection.add()
        conn.src = src
        conn.dst = dst
        conn.weight = weight

    # Process children
    for connection in node.parent_connections():
        conn = part.child.add()
        conn.src = connection.from_slot
        conn.dst = connection.to_slot
        _process_body_part(conn.part, connection.node, brain)

class Tree(object):
    """
    A tree to represent a robot that can be used for evolution.

    The tree class should really only be used to wrap frozen node
    structures, i.e. robot trees that will no longer be mutated.
    It maintains an internal
    """

    def __init__(self, root):
        """
        :param root:
        :type root: Node
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

    @staticmethod
    def from_body_brain(body, brain, body_spec):
        """
        Creates a tree from a body and a brain. Every neuron will need
        to have an assigned part ID in order for this to work.

        :param body:
        :type body: Body
        :param brain:
        :type brain: NeuralNetwork
        :type body_spec: BodyImplementation
        :param body_spec:
        :return:
        """
        # Generate neuron map, make sure every neuron is assigned to a part
        neuron_map = {}
        for neuron in brain.neuron:
            if not neuron.HasField("partId"):
                raise Exception("Neuron %s not associated with part." % neuron.id)

            neuron_map[neuron.id] = neuron

        # Create the tree without neural net connections
        root = _create_subtree(body.root, brain, body_spec)
        tree = Tree(root)

        # Create the neural net connections. We only
        # have the id <-> id paths, so we'll have to
        # locate the neurons in the tree and then
        # build the paths.
        for conn in brain.connection:
            src_neuron = neuron_map[conn.src]
            dst_neuron = neuron_map[conn.dst]
            src_node = tree.get_node(src_neuron.partId)
            dst_node = tree.get_node(dst_neuron.partId)
            src_node.add_neural_connection(src_neuron, dst_neuron, dst_node, conn.weight)

        return tree

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
        self.num_hidden = len([n for n in neurons if n.type == "Hidden"])

        # Check if given number of inputs / outputs matches spec
        inputs = len([n for n in neurons if n.layer == "input"])
        outputs = len([n for n in neurons if n.layer == "output"])
        if inputs != self.spec.inputs or outputs != self.spec.outputs:
            raise Exception("Part input / output mismatch.")

    def copy(self, copy_parent=True):
        """
        Returns a deep copy of this subtree
        :param copy_parent: If set to false, the parent connection of this node
                       is temporarily removed before copying to prevent it
                       from being copied as well. Useful if only the subtree
                       is needed. Note that this will result in the returned
                       copy being a root node.
        :type copy_parent: bool
        :return:
        :rtype: Node
        """
        old_conn = self.connections
        if not copy_parent:
            self.connections = {slot: self.connections[slot] for slot in self.connections
                                if self.connections[slot].parent}

        result = copy.deepcopy(self)
        self.connections = old_conn
        return result

    def set_connection(self, from_slot, to_slot, node, parent=True):
        """
        Adds a bidirectional node body connection, removing any connection
        that was currently there.
        """
        self.remove_connection(from_slot)
        self.connections[from_slot] = BodyConnection(from_slot, to_slot, node, parent)
        if parent:
            node.set_connection(to_slot, from_slot, self, parent=False)

    def remove_connection(self, from_slot):
        """
        Remove the connection at the given slot
        :param from_slot:
        :return:
        """
        conn = self.connections.get(from_slot, None)
        if not conn:
            return

        if conn.parent:
            conn.node.remove_connection(conn.to_slot)

        del self.connections[from_slot]

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
        return other.node.get_target(path[1:]) if other else None

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
        if target is self:
            return []

        for conn in self.connections.values():
            if conn.node is origin:
                continue

            path = conn.node.get_path(target, self)
            if path is not False:
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

    def get_neuron_id(self, neuron_layer, offset):
        """
        Convenience function to return the id corresponding to
        a neuron of a given type / offset. Note that this
        does not use the IDs of the current neurons, but rather
        returns the neuron ID as it will be after the robot
        has been generated.
        """
        t = {"input": "in", "output": "out", "hidden": "hidden"}[neuron_layer]
        return "%s-%s-%d" % (self.part.id, t, offset)

    def get_neuron_offset(self, neuron):
        """
        Returns the layer offset of the given neuron.
        :param neuron:
        :type neuron: Neuron
        :return:
        """
        offset = 0
        for other in self.neurons:
            if other is neuron:
                return offset

            if other.layer == neuron.layer:
                offset += 1

        return False

    def get_neural_connections(self):
        """
        Attempts to traverse neural connections and returns list
        of the ones that are valid as `src_id`, `dst_id`, weight triples.

        :return:
        :rtype: (str, str, float)
        """
        results = []
        taken = set()
        for conn in self.neural_connections:
            src_layer, src_idx = conn.src
            if not self.has_neuron(src_layer, src_idx):
                continue

            target = self.get_target(conn.path)
            if not target:
                continue

            dst_layer, dst_idx = conn.dst
            if not target.has_neuron(dst_layer, dst_idx):
                continue

            # Connection is possible
            src_id = self.get_neuron_id(src_layer, src_idx)
            dst_id = target.get_neuron_id(dst_layer, dst_idx)

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

        :return:
        :rtype: list[BodyConnection]
        """
        for v in self.connections.values():
            if not v.parent:
                continue

            yield v

    def child_connection(self):
        """
        Returns the connection this node uses to attach to
        its parent, or `None` if this node is the root node.
        :return:
        :rtype: BodyConnection
        """
        for v in self.connections.values():
            if not v.parent:
                return v

        return None

    def is_root(self):
        """
        Returns true if this node has no non-parent connections
        :return:
        """
        return self.child_connection() is None

    def __len__(self):
        """
        Returns the total number of nodes in the subtree for which
        this node is the root.

        :rtype: int
        :return: Subtree size
        """
        return sum(len(v.node) for v in self.parent_connections()) + 1

    def io_count(self):
        """
        Returns the number of inputs, outputs and hidden neurons
        specified by the subtree starting with this node.

        :return:
        :rtype: (int, int, int)
        """
        inputs, outputs, hidden = self.spec.inputs, self.spec.outputs, self.num_hidden
        for conn in self.parent_connections():
            i, o, h = conn.node.io_count()
            inputs += i
            outputs += o
            hidden += h

        return inputs, outputs, hidden

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
            (src.layer, src_offset),
            (dst.layer, dst_offset),
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
        :param src: (layer, offset) tuple
        :param dst: (layer, offset) tuple
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
