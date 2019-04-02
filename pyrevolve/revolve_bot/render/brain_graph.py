from graphviz import Digraph, render
# belong to TODO
import fnmatch


class BrainGraph:
    def __init__(self, brain, name='brain', typename='brain'):
        self.graph = Digraph(typename, filename=name, format='png')
        self.brain = brain

    def add_node(self, node_id, node_type, text):
        """
        Add node to graph
        @param node_id: id of node
        @param node_type: type of node
        @param text: text to show inside node
        """
        if node_type == 'Input':
            self.graph.attr('node', shape='circle')
        elif node_type == 'Oscillator':
            self.graph.attr('node', shape='square')
        self.graph.node(node_id, label=text)

    def add_edge(self, source_id, desitnation_id, label):
        """
        Add edge to graph
        @param source_id: id of source node
        @param destination_id: id of destination node
        @param label: label of edge
        """
        self.graph.edge(source_id, desitnation_id, label)

    def save_graph(self):
        """
        Save graph
        """
        self.graph.render()

    def brain_to_graph(self):
        """
        Export complete brain to graph
        """

        nodes = self.brain.nodes
        params = self.brain.params
        # belongs to TODO
        duplicates = fnmatch.filter(nodes, 'node*-*')
        for node in nodes:
            # TODO REMOVE condition WHEN duplicated nodes bug is fixed -- duplicated nodes end in '-[0-9]+' or '-core[0-9]+' (node2-2, node2-core1)
            if node not in duplicates:
                node_id = nodes[node].id
                text = node_id
                if node_id in params:
                    param = params[node_id]
                    text += '\n Oscillator {0} \n period: {1} \n phase_offset: {2} \n amplitude: {3}'.format(
                        nodes[node].part_id, params[node_id].period, params[node_id].phase_offset, params[node_id].amplitude)
                self.add_node(node_id, nodes[node].type, text)

        for connection in self.brain.connections:
            self.add_edge(str(connection.src), str(connection.dst), str(connection.weight))
