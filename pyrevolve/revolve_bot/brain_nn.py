"""
Class containing the brain parts to compose a robot
"""
from collections import OrderedDict

class BrainNN():
    """
    Base class allowing for constructing neural network controller components in an overviewable manner
    """

    def __init__(self):

        self.nodes = {}
        self.connections = []
        self.params = {}

    def FromYaml(self, yaml_object):
        """
        From a yaml object, creates a data struture of interconnected body modules. 
        Standard names for modules are: 
        """
        if 'neurons' not in yaml_object:
            raise KeyError('Network must have neurons.')

        if 'params' not in yaml_object:
            raise KeyError('Network must have params.')

        for k_node in yaml_object['neurons']:
            node = Node()
            node.generate_node(yaml_object['neurons'][k_node])
            self.nodes[k_node] = node

        if 'connections' in yaml_object:
            for edge in yaml_object['connections']:
                connection = Connection()
                connection.generate_connection(edge)
                self.connections.append(connection)

        for k_node in yaml_object['params']:
            params = Params()
            params.generate_params(yaml_object['params'][k_node])
            self.params[k_node] = node

        return [self.nodes, self.connections, self.params]



class Node():

    def __init__(self):

        self.id = None
        self.layer = None
        self.part_id = None
        self.type = None

    def generate_node(self, yaml_object_node):

        self.id = yaml_object_node['id']
        self.layer = yaml_object_node['layer']
        self.part_id = yaml_object_node['part_id']
        self.type = yaml_object_node['type']

        print('----')
        print(self.id)
        print(self.layer)
        print(self.part_id)
        print(self.type)

class Connection():

    def __init__(self):
        self.dst = None
        self.src = None
        self.weight = None

    def generate_connection(self, yaml_object_connection):

        self.dst = yaml_object_connection['dst']
        self.src = yaml_object_connection['src']
        self.weight = yaml_object_connection['weight']

        print('---------')
        print(self.dst)
        print(self.src)
        print(self.weight)


class Params():

    def __init__(self):
        self.period = None
        self.phase_offset = None
        self.amplitude = None
        self.bias = None
        self.gain = None

    def generate_params(self, yaml_object_node):

        if 'period' in yaml_object_node:
            self.period = yaml_object_node['period']
        if 'phase_offset' in yaml_object_node:
            self.phase_offset = yaml_object_node['phase_offset']
        if 'amplitude' in yaml_object_node:
            self.amplitude = yaml_object_node['amplitude']
        if 'bias' in yaml_object_node:
            self.bias = yaml_object_node['bias']
        if 'gain' in yaml_object_node:
            self.gain = yaml_object_node['gain']

        print('----')
        print(self.period)
        print(self.phase_offset)
        print(self.amplitude)
        print(self.bias)
        print(self.gain)