import math
import random

from pyrevolve.angle import Tree, Node
from pyrevolve.angle.robogen.spec import RobogenTreeGenerator
from pyrevolve.genotype.direct_tree.compound_mutation import DirectTreeNEATMutationConfig
from pyrevolve.genotype.direct_tree.direct_tree_neat_genotype import DirectTreeNEATGenotype
from pyrevolve.genotype.direct_tree.tree_helper import _node_list, _renumber, _delete_subtree
from pyrevolve.spec.msgs import Neuron, Robot, BodyPart
from pyrevolve.util import decide


class DirectTreeMutationConfig:
    def __init__(self):
        pass


class Mutator(object):
    """
    Parameter mutation class. Mutation is achieved by generating
    a new value for each parameter and combining it with the
    old parameter in the ratio specified by the parameter's
    epsilon value.
    """

    def __init__(self, robogen_tree_generator: RobogenTreeGenerator,
                 p_delete_hidden_neuron=0.05,
                 p_remove_brain_connection=0.05,
                 p_delete_subtree=0.05,
                 p_swap_subtree=0.05,
                 p_duplicate_subtree=0.05):
        """
        :param body_gen: A body generator for this robot.
        :type body_gen: BodyGenerator
        :param brain_gen: A neural net generator for this robot
        :type brain_gen: NeuralNetworkGenerator
        :return:
        """
        self.p_duplicate_subtree = p_duplicate_subtree
        self.p_swap_subtree = p_swap_subtree
        self.p_delete_subtree = p_delete_subtree
        self.p_delete_brain_connection = p_remove_brain_connection
        self.p_delete_hidden_neuron = p_delete_hidden_neuron
        self.robogen_tree_generator: RobogenTreeGenerator = robogen_tree_generator

    def mutate(self, genotype: DirectTreeNEATGenotype,
               mutation_conf: DirectTreeNEATMutationConfig, in_place=True):
        """
        Mutates the robot tree. This performs the following operations:
        - Body parameters are mutated
        - Brain parameters are mutated
        - A subtree might be removed
        - A subtree might be duplicated
        - Two subtrees might be swapped
        - Subtrees are duplicated at random
        - Body parts are added at random
        Mutation operations are designed to make changes to the robot
        whilst keeping it at roughly the same complexity. This means that:
        - The probability of a new body part being added is proportional
          to the average number of body parts being removed in a single
          step.
        - The number of newly created hidden neurons and neural connections
          equals the average number of neurons and connections removed in
          each step.
        :param tree:
        :type tree: Tree
        :param in_place:
        :return:
        """
        tree = genotype._body_genome

        root = tree.root if in_place else tree.root.copy()

        # First, we delete a random subtree (this might create some space)
        _, avg_del_len = self.delete_random_subtree(root)

        # Next, we duplicate a random subtree
        _, avg_dup_len = self.duplicate_random_subtree(root)

        # We then swap two random subtrees
        self.swap_random_subtrees(root)

        hidden_before = hidden_after = conn_before = conn_after = 0
        node_list = _node_list(root, root=True)
        p_keep_hidden_neuron = 1.0 - self.p_delete_hidden_neuron
        p_keep_neural_connection = 1.0 - self.p_delete_brain_connection
        for node in node_list:
            # Delete hidden neurons at random
            hidden_before += node.io_count(recursive=False)[2]
            node.set_neurons([neuron for neuron in node.get_neurons()
                              if neuron.layer != "hidden"
                              or decide(p_keep_hidden_neuron)])
            hidden_after += node.io_count(recursive=False)[2]

            # Delete brain connections at random
            connections = node.get_neural_connections()
            conn_before += len(connections)
            node.set_neural_connections([conn for conn in connections
                                         if decide(p_keep_neural_connection)])
            conn_after += len(node.get_neural_connections())

            # Mutate body and brain parameters
            self.mutate_node_body_parameters(node)
            self.mutate_node_brain_parameters(node)

        # We then add new hidden neurons. We don't want to bias
        # the number of hidden neurons through this procedure,
        # so we want to add, on average, as many as we remove,
        # though we don't want it to remain strictly the same.
        # We thus take the number of hidden neurons before
        # they were removed and multiply it by the deletion
        # probability. Cap to the maximum number we can add to
        # not violate robot properties
        n_new_hidden = \
            int(min(round(hidden_before * self.p_delete_hidden_neuron),
                    self.robogen_tree_generator.brain_gen.max_hidden - hidden_after))
        nodes = _node_list(root, root=True)
        for _ in range(n_new_hidden):
            target = random.choice(nodes)
            nw = Neuron()
            nw.layer = "hidden"
            nw.type = self.robogen_tree_generator.brain_gen.choose_neuron_type(nw.layer)
            spec = self.robogen_tree_generator.brain_gen.spec.get(nw.type)
            self.robogen_tree_generator.brain_gen.initialize_neuron(spec, nw)
            target.set_neurons(target.get_neurons() + [nw])

        # Finally, we add new neural connections, applying the same logic
        # as before for the count.
        n_new_connections = \
            int(round(conn_before * self.p_delete_brain_connection))
        sources = [(node, neuron) for node in nodes
                   for neuron in node.get_neurons()]
        targets = [(node, neuron) for node in nodes
                   for neuron in node.get_neurons()
                   if neuron.layer in ("hidden", "output")]

        # Can only add neural connections if there are connection sources and
        # targets
        if sources and targets:
            for i in range(n_new_connections):
                source_node, source_neuron = random.choice(sources)
                target_node, target_neuron = random.choice(targets)
                weight = self.robogen_tree_generator.brain_gen.choose_weight()
                source_node.add_neural_connection(source_neuron, target_neuron,
                                                  target_node, weight)

        # Next, we add a body part at random. To roughly maintain
        # robot complexity, we're making sure that the expected value
        # of the number of added body parts in the loop below equals
        # the expected value of the number of deleted parts.
        avg_parts_deleted = avg_del_len * self.p_delete_subtree \
                            - avg_dup_len * self.p_duplicate_subtree
        e_parts_to_add = \
            min(avg_parts_deleted, self.robogen_tree_generator.body_gen.max_parts - len(root))
        n_its = int(math.ceil(e_parts_to_add * 2))
        if n_its > 0:
            p_add_body_part = e_parts_to_add / n_its
            for _ in range(n_its):
                self.add_random_body_part(p_add_body_part, root)

        # Renumber the entire tree
        _renumber(root)

        new_genotype = genotype.clone()
        new_genotype._body_genome.root = tree #if in_place else Tree(root)

        return new_genotype

    def delete_random_subtree(self, root):
        """
        Deletes a subtree at random, assuming this is possible within
        the boundaries of the robot specification.
        :param root: Root node of the tree
        :return: The removed subtree (or None if no subtree was removed)
        :rtype: Node
        """
        node_list = _node_list(root, root=False)
        max_remove_size = len(node_list) + 1 - self.robogen_tree_generator.body_gen.min_parts
        items = [node for node in node_list if len(node) <= max_remove_size]
        if not items:
            return None, 0

        avg_del_len = sum(len(node) for node in items) / float(len(items))
        if not decide(self.p_delete_subtree):
            return None, avg_del_len

        subtree = random.choice(items)
        _delete_subtree(subtree)
        return subtree, avg_del_len

    def duplicate_random_subtree(self, root):
        """
        Picks a random subtree that can be duplicated within the robot
        boundaries, copies it and attaches it to a random free slot.
        :param root:
        :type root: Node
        :return:
        """
        node_list = _node_list(root, root=False)
        inputs, outputs, hidden = root.io_count()
        max_add_size = self.robogen_tree_generator.body_gen.max_parts - len(node_list) - 1

        # Create a list of subtrees that
        # - Is not larger than max_add_size
        # - Does not violate I/O constraints when added
        mi, mo, mh = self.robogen_tree_generator.body_gen.max_inputs, \
                     self.robogen_tree_generator.body_gen.max_outputs, \
                     self.robogen_tree_generator.brain_gen.max_hidden

        def valid_part(node):
            """
            :type node: Node
            """
            if len(node) > max_add_size:
                return False

            i, o, h = node.io_count()
            return (i + inputs) <= mi \
                   and (o + outputs) <= mo and (h + hidden) <= mh

        # If there are no valid nodes or attachment positions, duplication will
        # never happen and the average duplication length is 0. Deciding this
        # in parts cuts the calculation short making it faster.
        nodes = [node for node in node_list if valid_part(node)]
        if not nodes:
            return None, 0

        # Generate a list of attachment points
        node_list.append(root)
        attachments = [(node, slot) for node in node_list
                       for slot in node.get_free_slots()]

        if not attachments:
            return None, 0

        # Only duplicate with the given probability
        avg_dup_len = sum(len(node) for node in nodes)
        if not decide(self.p_duplicate_subtree):
            return None, avg_dup_len

        # Pick a random node to duplicate
        dup = random.choice(nodes)

        # We need a current protobuf body to call `choose_attachment`,
        # generate it here
        robot = Robot()
        _renumber(root)
        root.build(robot.body.root, robot.brain)

        attach_node, attach_slot = self.robogen_tree_generator.body_gen.choose_attachment(
                attachments=attachments,
                root_part=root.part)
        dup_new = dup.copy(copy_parent=False)
        dup_new.set_connection(
                from_slot=dup.parent_connection().from_slot,
                to_slot=attach_slot,
                node=attach_node,
                parent=False)
        return dup_new, avg_dup_len

    def swap_random_subtrees(self, root):
        """
        Picks to random subtrees (which are not parents / children of each
        other) and swaps them.
        :param root:
        :return: The two body parts on which swapping was performed,
                 or (None, None) if this did not happen.
        """
        if not decide(self.p_swap_subtree):
            return None, None

        nodes = _node_list(root, root=False)
        if not nodes:
            return None, None

        a = random.choice(nodes)
        """ :type : Node """

        related = set([a] + a.get_parents() + a.get_children())
        swaps = [node for node in nodes if node not in related]
        if not swaps:
            return None, None

        b = random.choice(swaps)
        """ :type : Node """

        a_conn = a.parent_connection()
        b_conn = b.parent_connection()

        # Sever existing connections
        a.remove_connection(a_conn.from_slot)
        b.remove_connection(b_conn.from_slot)

        # Create new connections
        a.set_connection(
                from_slot=a_conn.from_slot,
                to_slot=b_conn.to_slot,
                node=b_conn.node,
                parent=False)
        b.set_connection(
                from_slot=b_conn.from_slot,
                to_slot=a_conn.to_slot,
                node=a_conn.node,
                parent=False)

    def add_random_body_part(self, prob, root):
        """
        Generates a new random body part
        :param prob: The probability with which the part should be added
        :param root:
        :return: The added body part
        """
        if not decide(prob):
            return None

        # Generator functions need the robot body, so we call renumber
        # and `build` in order to have the internal node structure represent
        # the final structure. We ignore the built brain.
        _renumber(root)
        robot = Robot()
        root.build(robot.body.root, robot.brain)

        nodes = _node_list(root, root=True)
        n_nodes = len(nodes)
        inputs, outputs, hidden = root.io_count(nodes)
        usable = self.robogen_tree_generator.body_gen.get_allowed_parts(
                attach_specs=self.robogen_tree_generator.body_gen.attach_specs,
                num_parts=n_nodes,
                inputs=inputs,
                outputs=outputs,
                root_part=root.part)
        if not usable:
            return None

        free = [(node, slot) for node in nodes
                for slot in node.get_free_slots()]

        if not free:
            return None

        # Pick a random attachment position to attach the new node
        parent_node, slot = random.choice(free)

        # Choose a body part type and initialize its parameters
        part = BodyPart()
        part.type = self.robogen_tree_generator.body_gen.choose_part(
                parts=usable,
                parent_part=parent_node.part,
                root_part=root.part,
                root=False)
        type_spec = self.robogen_tree_generator.body_gen.spec.get(part.type)
        self.robogen_tree_generator.body_gen.initialize_part(
                spec=type_spec,
                new_part=part,
                parent_part=parent_node.part,
                root_part=root.part,
                root=False)

        # Decide the initial hidden neurons this part will have
        # by getting the average of an expected number from
        # the brain generator. Cap it to the maximum allowed number.
        n_hidden = int(round(self.robogen_tree_generator.brain_gen.choose_num_hidden() / float(n_nodes)))
        n_hidden = min(self.robogen_tree_generator.brain_gen.max_hidden - hidden, n_hidden)

        # We can hijack brain generation to generate a neural network for
        # just this part. We then only have to generate the network connections.
        inputs = ["input-{}".format(i) for i in range(type_spec.inputs)]
        outputs = ["output-{}".format(i) for i in range(type_spec.outputs)]
        network = self.robogen_tree_generator.brain_gen.generate(inputs, outputs, num_hidden=n_hidden)
        neurons = [neuron for neuron in network.neuron]

        # Create the new node object
        nw_node = Node(part, neurons, self.robogen_tree_generator.body_gen.spec)
        nodes.append(nw_node)

        # Pick a target slot
        target_slot = self.robogen_tree_generator.body_gen.choose_target_slot(
                new_part=type_spec,
                parent=parent_node.part,
                root_part=root.part)
        parent_node.set_connection(slot, target_slot, nw_node)

        # Now we add network connections where this node is the source. We
        # don't add connections towards this node since, assuming valid
        # paths, these connections already exist in other nodes.
        sources = neurons
        destinations = [(neuron, node) for node in nodes
                        for neuron in node.get_neurons()
                        if neuron.layer in ("hidden", "output")]
        for src, (dst, dst_node) in zip(sources, destinations):
            if not decide(self.robogen_tree_generator.brain_gen.conn_prob):
                continue

            weight = self.robogen_tree_generator.brain_gen.choose_weight()
            nw_node.add_neural_connection(src, dst, dst_node, weight)

        return nw_node

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
        spec = self.robogen_tree_generator.body_gen.spec.get(node.part.type)
        nw_params = spec.get_epsilon_mutated_parameters(
                params=node.part.param,
                serialize=False)
        spec.set_parameters(node.part.param, nw_params)

    def mutate_node_brain_parameters(self, node):
        """
        :param node:
        :type node: Node
        :return:
        """
        for neuron in node.get_neurons():
            spec = self.robogen_tree_generator.brain_gen.spec.get(neuron.type)
            nw_params = spec.get_epsilon_mutated_parameters(
                    params=neuron.param,
                    serialize=False)
            spec.set_parameters(neuron.param, nw_params)