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

    def __init__(self, spec=None):
        """
        :param spec:
        :type spec: dict
        :return:
        """
        self.spec = {} if spec is None else spec
        self.aliases = {}

        _process_aliases(self.spec, self.aliases)

    def get(self, part_type):
        """
        Returns the part settings corresponding to the given type
        :param part_type:
        :type part_type: str
        :return: PartSpec implementation spec, or None if not found
        :rtype: PartSpec
        """
        key = self.aliases.get(part_type, part_type)
        return self.spec.get(key, None)

    def set(self, type_name, spec):
        """
        :param type_name:
        :type type_name: str
        :param spec:
        :type spec: Parameterizable
        :return:
        """
        self.spec[type_name] = spec
        _process_aliases(self.spec, self.aliases)


class BodyImplementation(SpecImplementation):
    """
    The BodyImplementation just inhertits from `SpecImplementation`
    verbatim.
    """


class NeuralNetImplementation(SpecImplementation):
    """
    This is the sample Neural Network implementation, which
    requires knowledge of the body to function.
    """
    def __init__(self, spec=None):
        """
        :param spec:
        :type spec: dict
        :return:
        """
        super(NeuralNetImplementation, self).__init__(spec)

        # Add default input neuron type
        if "Input" not in self.spec:
            self.set("Input", NeuronSpec())


def default_neural_net():
    """
    Returns the neural net implementation for the default
    neural net shipped with Revolve
    :return:
    :rtype: NeuralNetImplementation
    """
    return NeuralNetImplementation({
        "Sigmoid": NeuronSpec(
            params=["bias", "gain"]
        ),
        "Simple": NeuronSpec(
            params=["bias", "gain"]
        ),
        "Oscillator": NeuronSpec(
            params=["period", "phase_offset", "amplitude"]
        )
    })


class ParamSpec(object):
    """
    Parameter specification class
    """
    def __init__(self, name, default=0.0, min_value=None, max_value=None, min_inclusive=True, max_inclusive=True):
        """
        :param default:
        :param min_value:
        :param max_value:
        :param min_inclusive:
        :param max_inclusive:
        """
        self.name = name
        self.min = min_value
        self.max = max_value
        self.min_inclusive = min_inclusive
        self.max_inclusive = max_inclusive
        self.default = default

    def is_valid(self, value):
        """
        Returns whether the given parameter is valid according to this param spec.

        :param value:
        :type value: float
        :return:
        :rtype: bool
        """
        min_valid = max_valid = True
        if self.min is not None:
            min_valid = value >= self.min and (self.min_inclusive or value > self.min)

        if self.max is not None:
            max_valid = value <= self.max and (self.max_inclusive or value < self.max)

        return min_valid and max_valid


class Parameterizable(object):
    """
    Parent class for objects with a parameter list that can be
    (un)serialized.
    """
    # Reserved parameters
    RESERVED = {'arity', 'type'}

    def __init__(self, params=None):
        """
        :param params: List of named params for this part, in the order in which they
                       will be serialized.
        :type params: list
        """
        if params is None:
            params = []

        l = self.n_parameters = len(params)

        # Map from parameter name to index in list
        for i in range(l):
            if not isinstance(params[i], ParamSpec):
                params[i] = ParamSpec(params[i])

            if params[i].name in self.RESERVED:
                err("'%s' is a reserved parameter and cannot be used as a name." % params[i].name)

        # Store tuple array index, spec
        self.parameters = {params[i].name: (i, params[i]) for i in range(l)}

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
        for k in self.parameters:
            ret[self.parameters[k][0]] = params.get(k, self.parameters[k][1].default)

        return ret

    def unserialize_params(self, params):
        """
        Unserializes a protobuf parameter array into a dictionary
        :param: params:
        :type params: list
        :return: Dictionary of unserialized params
        :rtype: dict
        """
        assert len(params) == len(self.parameters), "Invalid parameter length."
        return {param: params[self.parameters[param][0]].value for param in self.parameters}

    def params_validate(self, params):
        """
        Check whether the given parameter dict is valid.
        :param params: Serialized or unserialized parameters
        :return:
        """
        if not isinstance(params, dict):
            params = self.unserialize_params(params)

        validates = True
        for param in params:
            if not self.parameters[param][1].is_valid(params[param]):
                validates = False
                break

        return validates


class PartSpec(Parameterizable):
    """
    Class used to specify all configurable details about a part.
    """

    def __init__(self, body_part=None, arity=0, inputs=0,
                 outputs=0, params=None):
        """

        :param body_part: Builder component, for whatever builder is being used
        :param arity: Arity (i.e. number of connection slots) of the body part
        :type arity: int
        :param inputs: Number of input neurons of this body part
        :type inputs: int
        :param outputs: Number of output neurons of this part
        :type outputs: int
        :return:
        """
        super(PartSpec, self).__init__(params)

        self.body_part = body_part
        self.arity = arity
        self.inputs = inputs
        self.outputs = outputs


class NeuronSpec(Parameterizable):
    """
    Specifies a configurable Neuron
    """