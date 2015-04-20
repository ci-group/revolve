def process_aliases(obj, alias_map):
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

        process_aliases(self.parts, self.part_aliases)
        process_aliases(self.neurons, self.neuron_aliases)

        # Add default simple neuron
        if "simple" not in neurons:
            self.set_neuron("Simple", Neuron(["bias"]))

    def get_part(self, part_type):
        """
        Returns the part settings corresponding to the given type
        :param part_type:
        :type part_type: str
        :return: Part implementation spec, or None if not found
        :rtype: Part
        """
        key = self.part_aliases.get(part_type, part_type)
        return self.parts.get(key, None)

    def get_neuron(self, neuron_type):
        """
        Returns the neuron settings corresponding to the given type.

        :param neuron_type:
        :type neuron_type: str
        :return: Neuron implementation spec, or None if not found
        :rtype: Neuron
        """
        key = self.part_aliases.get(neuron_type, neuron_type)
        return self.neurons.get(key, None)

    def set_neuron(self, neuron_type, neuron):
        """
        :param neuron_type:
        :type neuron_type: str
        :param neuron:
        :type neuron: Neuron
        :return:
        """
        self.neurons[neuron_type] = neuron
        process_aliases(self.parts, self.part_aliases)

    def set_part(self, part_type, part):
        """
        :param part_type:
        :type part_type: str
        :param part:
        :type part: Part
        :return:
        """
        self.neurons[part_type] = part
        process_aliases(self.neurons, self.neuron_aliases)


class Parameterizable(object):
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

        self.defaults = {k: 0.0 for k in params}
        if defaults is not None:
            self.defaults.update(defaults)

    def serialize_params(self, params):
        """
        Serializes the given parameter object into an array
        that can be used to add to protobuf.
        """
        ret = [0] * self.n_parameters
        for k in self.defaults:
            ret[self.parameters[k]] = params[k] if k in params else self.defaults[k]

        return ret


class Part(Parameterizable):
    """
    Class used to specify all configurable details about a part.
    """

    def __init__(self, component=None, arity=0, input_neurons=0,
                 output_neurons=0, params=None, defaults=None):
        """

        :param component: Builder component
        :type component: Component
        :param arity: Arity (i.e. number of slots) of the body part
        :type arity: int
        :param input_neurons: Number of input neurons of this body part
        :type input_neurons: int
        :param output_neurons: Number of output neurons of this part
        :type output_neurons: int
        :return:
        """
        super(Part, self).__init__(params, defaults)

        self.component = component
        self.arity = arity
        self.input_neurons = input_neurons
        self.output_neurons = output_neurons


class Neuron(Parameterizable):
    """
    Specifies a configurable Neuron
    """
    pass