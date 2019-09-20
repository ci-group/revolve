from graphviz import Digraph, render
# belong to TODO
import fnmatch
import re
import os


class BrainGraph:
    def __init__(self, brain, name='brain', typename='brain'):
        name, ext = os.path.splitext(name)
        if ext == '' or ext == '.png':
            format = 'png'
        else:
            format = ext[1:]

        self.graph = Digraph(typename, filename=name, format=format, node_attr={'margin': '0'})
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
        self.graph.edge(str(source_id), str(desitnation_id), str(label))

    def save_graph(self):
        """
        Save graph
        """
        self.graph.render(cleanup=True)

    def brain_to_graph(self, round_params=False, decimals=4):
        """
        Export complete brain to graph
        @param round_params: round parameters if True
        @param decimals: decimals to round
        """

        nodes = self.brain.nodes
        params = self.brain.params
        # belongs to TODO
        duplicates = fnmatch.filter(nodes, 'node*-*')
        for node in nodes:
            # TODO REMOVE condition WHEN duplicated nodes bug is fixed -- duplicated nodes end in '-[0-9]+' or '-core[0-9]+' (node2-2, node2-core1)
            if node not in duplicates:
                node_id = nodes[node].id
                text = node_id + '\n'
                if nodes[node].type == 'Oscillator':
                    text += 'Oscillator \n {}'.format(nodes[node].part_id)
                elif nodes[node].type == 'Input':
                    text += 'Sensor \n {}'.format(nodes[node].part_id)
                if node_id in params:
                    if params[node_id].period is not None:
                        period = round(float(params[node_id].period), decimals) if round_params else float(params[node_id].period)
                        text += '\n period: {0}'.format(period)
                    if params[node_id].phase_offset is not None:
                        phase_offset = round(float(params[node_id].phase_offset), decimals) if round_params else float(params[node_id].phase_offset)
                        text += '\n phase_offset: {0}'.format(phase_offset)
                    if params[node_id].amplitude is not None:
                        amplitude = round(float(params[node_id].amplitude), decimals) if round_params else float(params[node_id].amplitude)
                        text += '\n amplitude: {0}'.format(amplitude)
                    if params[node_id].bias is not None:
                        bias = round(float(params[node_id].bias), decimals) if round_params else float(params[node_id].bias)
                        text += '\n bias: {0}'.format(bias)
                    if params[node_id].gain is not None:
                        gain = round(float(params[node_id].gain), decimals) if round_params else float(params[node_id].gain)
                        text += '\n gain: {0}'.format(gain)

                self.add_node(node_id, nodes[node].type, text)

        for connection in self.brain.connections:
            if round_params:
                self.add_edge(connection.src, connection.dst, round(float(connection.weight), decimals))
            else:
                self.add_edge(connection.src, connection.dst, float(connection.weight))
