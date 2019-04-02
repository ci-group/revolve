"""
Class containing the brain parts to compose a robot
"""
from collections import OrderedDict


class BrainNN:
    """
    Base class allowing for constructing neural network controller components in an overviewable manner
    """

    def __init__(self):
        self.nodes = {}
        self.connections = []
        self.params = {}

    @staticmethod
    def FromYaml(yaml_object):
        """
        From a yaml object, creates a data struture of interconnected body modules. 
        Standard names for modules are: 
        """
        brain = BrainNN()

        if 'neurons' not in yaml_object:
            raise KeyError('Network must have nodes.')

        if 'params' not in yaml_object:
            raise KeyError('Network must have params.')

        for k_node in yaml_object['neurons']:
            node = Node()
            node.generate_node(yaml_object['neurons'][k_node])
            brain.nodes[k_node] = node

        if 'connections' in yaml_object:
            for edge in yaml_object['connections']:
                connection = Connection()
                connection.generate_connection(edge)
                brain.connections.append(connection)

        for k_node in yaml_object['params']:
            params = Params()
            params.generate_params(yaml_object['params'][k_node])
            brain.params[k_node] = params

        return brain

    def to_yaml(self):
        yaml_dict_brain = OrderedDict()

        yaml_dict_neurons = OrderedDict()
        for node in self.nodes:
            yaml_dict_neurons[node] = { 
                'id': self.nodes[node].id,
                'layer': self.nodes[node].layer,
                'part_id': self.nodes[node].part_id,
                'type': self.nodes[node].type
            }
        yaml_dict_brain['neurons'] = yaml_dict_neurons

        yaml_dict_connections = []
        if self.connections:
            for edge in self.connections:
                yaml_dict_connections.append({ 
                    'dst': edge.dst,
                    'src': edge.src,
                    'weight': edge.weight,
                })
                
            yaml_dict_brain['connections'] = yaml_dict_connections

        yaml_dict_params = OrderedDict()
        for node in self.params:
            yaml_dict_params[node] = {}

            if self.params[node].bias is not None:
                yaml_dict_params[node]['bias'] = self.params[node].bias
                
            if self.params[node].gain is not None:
                yaml_dict_params[node]['gain'] = self.params[node].gain
                
            if self.params[node].period is not None:
                yaml_dict_params[node]['period'] = self.params[node].period
                
            if self.params[node].phase_offset is not None:
                yaml_dict_params[node]['phase_offset'] = self.params[node].phase_offset
                
            if self.params[node].amplitude is not None:
                yaml_dict_params[node]['amplitude'] = self.params[node].amplitude

        yaml_dict_brain['params'] = yaml_dict_params

        return yaml_dict_brain


class Node:
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


class Connection:
    def __init__(self):
        self.dst = None
        self.src = None
        self.weight = None

    def generate_connection(self, yaml_object_connection):

        self.dst = yaml_object_connection['dst']
        self.src = yaml_object_connection['src']
        self.weight = yaml_object_connection['weight']


class Params:
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
