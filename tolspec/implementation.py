class SpecImplementation(object):
    """

    """
    def __init__(self, parts=None, neurons=None):
        self.parts = {} if parts is None else parts
        self.neurons = {} if neurons is None else neurons

    def get_part(self, part_type):
        """
        Returns the part corresponding to the given type

        :return: Part implementation spec, or None
        :rtype: Part
        """
        return self.parts[part_type] if part_type in self.parts else None


class Parameterizable(object):
    def __init__(self, parameters=None, defaults=None):
        """
        :param parameters: List of named parameters for this part
        :type parameters: list
        :param defaults: Dictionary of default parameter values
        :type defaults: dict
        """
        if parameters is None:
            parameters = []

        l = self.n_parameters = len(parameters)

        # Map from parameter name to index in list
        self.parameters = {parameters[i]: i for i in range(l)}

        self.defaults = {k: 0.0 for k in parameters}
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

    def __init__(self, component, arity=0, input_neurons=0,
                 output_neurons=0, parameters=None, defaults=None):
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
        super(Part, self).__init__(parameters, defaults)

        self.component = component
        self.arity = arity
        self.input_neurons = input_neurons
        self.output_neurons = output_neurons


class Neuron(Parameterizable):
    """
    Specifies a configurable Neuron
    """
    pass