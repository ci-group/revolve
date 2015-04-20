import yaml
from ..tol_pb2 import *
from ..implementation import SpecImplementation, Part, Neuron


def err(msg):
    """
    Simple internal error function
    :param msg:
    :return:
    """
    raise ValueError("Error: %s" % msg)


class YamlToProtobuf:
    """

    """
    def __init__(self, spec, lines):
        """
        :param spec:
        :type spec: SpecImplementation
        :param lines:
        :type lines: iterable
        :return:
        """
        # TODO This could be more efficient...
        contents = '\n'.join([l for l in lines])
        obj = yaml.parse(contents)
        self.spec = spec

        self.part_ids = set()
        self.robot = Robot()

        self.robot.id = obj.get('id', 0)

        if 'body' not in obj:
            err("Missing robot 'body'.")

        self.neurons = {}

        self.robot.brain = Brain()
        self.robot.root = self._process_body_part(obj['body'])

        brain = obj.get('brain', {})
        neurons = brain.get('neurons', [])
        connections = brain.get('connections', [])
        params = brain.get('params', {})



    def _process_body_part(self, conf, dest_slot=None):
        """
        :param conf:
        :return:
        :rtype: BodyPart
        """
        part = BodyPart()

        if 'id' not in conf:
            err("Missing part ID.")

        part_id = conf['id']
        if part_id in self.part_ids:
            err("Duplicate part ID '%s'" % part_id)
        self.part_ids.add(part_id)

        if 'type' not in conf:
            err("Missing part type.")
        part_type = conf['type']

        spec = self.spec.get_part(part_type)
        if spec is None:
            err("Part type '%s' not in implementation spec." % part_type)

        # Add part parameters
        part.orientation = conf.get('orientation', 0)
        params = spec.serialize_params(conf.get('params', {}))
        for param in params:
            p = part.params.add()
            p.value = param

        # Add children
        children = conf.get('children', {})
        for src in children:
            if src == dest_slot:
                err("Part '%s': Attempt to use slot %d attached to root for child."
                    % (part_id, src))
            self._process_body_connection(part, src, children[src])

        # Add automatic input / output neurons
        for i in range(spec.input_neurons):
            neuron_id = "%s-in-%d" % (part_id, i)
            if neuron_id in self.neurons:
                err("Duplicate neuron ID '%s'" % neuron_id)

            self.neurons[neuron_id] = {
                "id": neuron_id,
                "layer": "input",
                "type": "simple"
            }

        for i in range(spec.output_neurons):
            neuron_id = "%s-out-%d" % (part_id, i)
            if neuron_id in self.neurons:
                err("Duplicate neuron ID '%s'" % neuron_id)

            self.neurons[neuron_id] = {
                "id": neuron_id,
                "layer": "output",
                "type": "simple"
            }

        return part

    def _process_body_connection(self, part, src, conf):
        """
        :param part:
        :type part: BodyPart
        :param src: Slot
        :type src: int
        :param conf:
        :return:
        :rtype: BodyConnection
        """
        conn = part.children.add()
        conn.src = src
        conn.dest = conf['slot'] if 'slot' in conf else 0
        conn.part = self._process_body_part(conf)

    def _create_neurons(self, neurons):
        """
        Creates hidden neurons.
        :return:
        """
