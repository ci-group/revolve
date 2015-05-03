from .exception import err
from .protobuf import BodyPart


def _process_aliases(obj, alias_map):
    """
    :param obj:
    :type obj: dict
    :param alias_map:
    :type alias_map: dict
    :return:
    """
    keys = obj.keys()

    for key in keys:
        if not isinstance(key, tuple):
            continue

        alias_map.update({alias: key for alias in key})


class SpecImplementation(object):
    """
    The SpecImplementation class is used to specify the implementation
    details of your brain / body space in the ToL spec. It tells what
    body parts / neuron types there are, and what their parameters are.
    """

    def __init__(self, parts=None, neurons=None):
        """
        :param parts:
        :param neurons:
        :return:
        """
        self.parts = {} if parts is None else parts
        self.neurons = {} if neurons is None else neurons

        self.part_aliases = {}
        self.neuron_aliases = {}

        _process_aliases(self.parts, self.part_aliases)
        _process_aliases(self.neurons, self.neuron_aliases)

        # Add default simple neuron
        if "simple" not in self.neurons:
            self.set_neuron("Simple", NeuronSpec(["bias"]))

    def get_part(self, part_type):
        """
        Returns the part settings corresponding to the given type
        :param part_type:
        :type part_type: str
        :return: PartSpec implementation spec, or None if not found
        :rtype: PartSpec
        """
        key = self.part_aliases.get(part_type, part_type)
        return self.parts.get(key, None)

    def get_neuron(self, neuron_type):
        """
        Returns the neuron settings corresponding to the given type.

        :param neuron_type:
        :type neuron_type: str
        :return: NeuronSpec implementation spec, or None if not found
        :rtype: NeuronSpec
        """
        key = self.part_aliases.get(neuron_type, neuron_type)
        return self.neurons.get(key, None)

    def set_neuron(self, neuron_type, neuron):
        """
        :param neuron_type:
        :type neuron_type: str
        :param neuron:
        :type neuron: NeuronSpec
        :return:
        """
        self.neurons[neuron_type] = neuron
        _process_aliases(self.parts, self.part_aliases)

    def set_part(self, part_type, part):
        """
        :param part_type:
        :type part_type: str
        :param part:
        :type part: PartSpec
        :return:
        """
        self.neurons[part_type] = part
        _process_aliases(self.neurons, self.neuron_aliases)


class Parameterizable(object):
    """
    Parent class for objects with a parameter list that can be
    (un)serialized.
    """
    # Reserved parameters
    RESERVED = ['arity', 'type']

    def __init__(self, params=None, defaults=None):
        """
        :param params: List of named params for this part
        :type params: list
        :param defaults: Dictionary of default parameter values
        :type defaults: dict
        """
        if params is None:
            params = []

        l = self.n_parameters = len(params)

        # Map from parameter name to index in list
        self.parameters = {params[i]: i for i in range(l)}

        for p in self.RESERVED:
            if p in self.parameters:
                err("'%s' is a reserved parameter and cannot be used as a name." % p)

        self.defaults = {k: 0.0 for k in params}
        if defaults is not None:
            self.defaults.update(defaults)

    def serialize_params(self, params):
        """
        Serializes the given parameter object into an array
        that can be used to add to protobuf.

        :param params:
        :type params: dict
        :return:
        :rtype: list
        """
        ret = [0] * self.n_parameters
        for k in self.defaults:
            ret[self.parameters[k]] = params.get(k, self.defaults[k])

        return ret

    def unserialize_params(self, params):
        """
        Unserializes a protobuf parameter array into
        :return: Dictionary of unserialized params
        :rtype: dict
        """
        assert len(params) == len(self.parameters), "Invalid parameter length."
        return {param: params[self.parameters[param]] for param in self.parameters}


class PartSpec(Parameterizable):
    """
    Class used to specify all configurable details about a part.
    """

    def __init__(self, body_part=None, arity=0, input_neurons=0,
                 output_neurons=0, params=None, defaults=None):
        """

        :param body_part: Builder component, for whatever builder is being used
        :param arity: Arity (i.e. number of connection slots) of the body part
        :type arity: int
        :param input_neurons: Number of input neurons of this body part
        :type input_neurons: int
        :param output_neurons: Number of output neurons of this part
        :type output_neurons: int
        :return:
        """
        super(PartSpec, self).__init__(params, defaults)

        self.body_part = body_part
        self.arity = arity
        self.input_neurons = input_neurons
        self.output_neurons = output_neurons


class NeuronSpec(Parameterizable):
    """
    Specifies a configurable Neuron
    """
    pass