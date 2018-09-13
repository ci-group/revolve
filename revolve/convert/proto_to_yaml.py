from ..spec import BodyImplementation, NeuralNetImplementation
from ..spec.msgs import Body, BodyPart, NeuralNetwork
from ..spec.exception import err


class BodyEncoder:
    """
    Body decoder for the protobuf messages
    """
    def __init__(self, spec):
        """
        :param spec:
        :type spec: BodyImplementation
        :return:
        """
        self.spec = spec
        self.unique_ids = set()

    # parse protobuf body into a dictionary
    def parse_body(self, body):
        """
        :param body
        :type protobuf body
        :return:
        """
        yaml_body = {}
        self._parse_part(yaml_body, body)
        return yaml_body


    def _parse_part(self, yaml_part, part, dst_slot = None):
        """
        :param yaml_part:
        :type yaml structure that the given protobuf part will be written to
        :param part
        :type protobuf part
        :param dst_slot
        :return:
        """
        part_id = part.id

        # check for duplicate part ids:
        if part_id in self.unique_ids:
            err("Duplicate part ID '{}'".format(part_id))
        self.unique_ids.add(part_id)

        if len(part_id) is 0:
            err("Missing part ID.")

        yaml_part['id'] = part_id
        yaml_part['type'] = part_type = part.type
        yaml_part['orientation'] = part.orientation
        yaml_part['label'] = part.label

        spec = self.spec.get(part_type)

        # check if part type is in spec:
        if spec is None:
            err("Part type '{}' not in implementation spec.".format(part_type))

        # Check destination slot arity
        if dst_slot is not None and dst_slot >= spec.arity:
            err("Cannot attach part '%s' with arity %d at slot %d" %
                (part_id, spec.arity, dst_slot))

        params = spec.unserialize_params(part.param)
        yaml_part['params'] = params

        connections = part.child

        if len(connections) > 0:

            yaml_part['children'] = {}

            for connection in connections:
                conn_src = connection.src

                if conn_src >= spec.arity:
                    err("Cannot attach to slot %d of part '{}' with arity "
                        "{}.".format(conn_src, part_id, spec.arity))

                if conn_src == dst_slot:
                    err("Part '{}': Attempt to use slot {} for child which is "
                        "already attached to parent.".format(part_id, conn_src))

                self._process_body_connection(connection, yaml_part)

    def _process_body_connection(self, connection, yaml_part):
        conn_src = connection.src
        conn_dst = connection.dst
        conn_part = connection.part

        if conn_src is None:
            err("Neuron connection is missing 'src'.")

        if conn_dst is None:
            err("Neuron connection is missing 'dst'.")

        # add child to parent:
        yaml_part['children'][conn_src] = {}
        yaml_child_part = yaml_part['children'][conn_src]

        # set child part:
        self._parse_part(yaml_child_part, conn_part, conn_dst)

        yaml_child_part['slot'] = conn_dst


class NeuralNetworkEncoder:
    """
    Encoder class for the standard neural network spec.
    """
    def __init__(self, spec):
        """
        :param spec:
        :type spec: NeuralNetImplementation
        :return:
        """
        self.spec = spec
        self.neurons = {}
        self.connections = []
        self.params = {}

    def parse_neural_network(self, network):
        """
        :param network:
        :type protobuf brain specification
        :return:
        """
        yaml_network = {}

        neurons = network.neuron
        connections = network.connection

        self._parse_neurons(neurons)
        self._parse_connections(connections)
        yaml_network['neurons'] = self.neurons
        yaml_network['connections'] = self.connections
        yaml_network['params'] = self.params
        return yaml_network

    def _parse_neurons(self, neurons):
        """
        :param neurons:
        :type protobuf neurons
        :return:
        """
        for neuron in neurons:
            neuron_id = neuron.id
            neuron_layer = neuron.layer
            neuron_type = neuron.type
            neuron_part_id = neuron.partId

            if neuron_id in self.neurons:
                err("Duplicate neuron ID '{}'".format(neuron_id))

            spec = self.spec.get(neuron_type)
            if spec is None:
                err("Unknown neuron type '{}'".format(neuron_type))
            neuron_params = spec.unserialize_params(neuron.param)

            self.neurons[neuron_id] = {
                "id": neuron_id,
                "layer": neuron_layer,
                "type": neuron_type,
                "part_id": neuron_part_id
                #"params": neuron_params
            }

            if len(neuron_params) is not 0:
                self.params[neuron_id] = neuron_params

    def _parse_connections(self, connections):
        """
        :param neurons:
        :type protobuf connections
        :return:
        """
        for conn in connections:
            conn_src = conn.src
            conn_dst = conn.dst
            conn_weight = conn.weight

            self.connections.append({
                'src': conn_src,
                'dst': conn_dst,
                'weight': conn_weight
            })


