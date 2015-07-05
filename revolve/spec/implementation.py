from __future__ import print_function
import random
from .exception import err
from .msgs import BodyPart

try:
    basestring
except NameError:
    basestring = str


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
        :return: Implementation spec, or None if not found
        :rtype: Parameterizable
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

    def get_all_types(self):
        """
        Returns a list of (the first aliases of) all
        spec identifiers.
        :return: A list of all spec identifiers
        :rtype list:
        """
        return [(a if isinstance(a, basestring) else a[0]) for a in self.spec.keys()]


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
            self.set("Input", NeuronSpec(layers=("input",)))


def default_neural_net():
    """
    Returns the neural net implementation for the default
    neural net shipped with Revolve
    :return:
    :rtype: NeuralNetImplementation
    """
    return NeuralNetImplementation({
        "Input": NeuronSpec(
            layers=["input"]
        ),
        "Sigmoid": NeuronSpec(
            params=[
                ParamSpec("bias", min_value=-10, max_value=10),
                ParamSpec("gain", min_value=-10, max_value=10, default=1.0)
            ],
            layers=["output", "hidden"]
        ),
        "Simple": NeuronSpec(
            params=[
                ParamSpec("bias", min_value=-10, max_value=10),
                ParamSpec("gain", min_value=-10, max_value=10, default=1.0)
            ],
            layers=["output", "hidden"]
        ),
        "Oscillator": NeuronSpec(
            params=[
                ParamSpec("period", min_value=0, max_value=50),
                ParamSpec("phase_offset", min_value=0, max_value=3.14),
                ParamSpec("amplitude", min_value=0, default=1, max_value=10)
            ],
            layers=["output", "hidden"]
        )
    })


class ParamSpec(object):
    """
    Parameter specification class
    """
    def __init__(self, name, default=0.0, min_value=None, max_value=None,
                 min_inclusive=True, max_inclusive=True, epsilon=0):
        """
        :param default:
        :param min_value:
        :param max_value:
        :param min_inclusive:
        :param max_inclusive:
        :param epsilon: The maximum fraction of mutation that may happen
                        to this parameter's value at any given time.
        """
        self.epsilon = epsilon
        self.name = name
        self.min = min_value
        self.max = max_value

        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("Parameter min value is larger than parameter max value.")

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

    def get_random_value(self, epsilon=1e-9):
        """
        Returns a random value according to this parameter spec. By default, this
        returns a uniformly distributed value between the minimum and the maximum
        value. If no minimum or maximum are supplied, the default value is returned.

        The uniform distribution has a small chance of generating a boundary value,
        if this happens while the boundary should not be included, the given epsilon
        value is added or subtracted to get the value within range.

        :param epsilon: See method description.
        :type epsilon: float
        :return: The generated value
        :rtype: float
        """
        if self.min is None or self.max is None:
            return self.default

        value = random.uniform(self.min, self.max)
        if value == self.min and not self.min_inclusive:
            value += epsilon
        elif value == self.max and not self.max_inclusive:
            value -= epsilon

        return value


class NormalDistParamSpec(ParamSpec):
    """
    Parameter spec for a normally distributed parameter, mostly serves
    generation purposes. No min / max values can be specified in the
    constructor (because that generally makes no sense for a normally
    distributed var).
    """
    def __init__(self, name, mean=0.0, stddev=1.0, default=0.0):
        """
        """
        super(NormalDistParamSpec, self).__init__(name, default=default)
        self.mean = mean
        self.stddev = stddev

    def get_random_value(self, epsilon=1e-9):
        """
        Random initialisation with mean and standard deviation.
        """
        return random.gauss(self.mean, self.stddev)


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

    def get_spec(self, param_name):
        """
        Returns the ParamSpec for the given parameter.
        :param param_name:
        :type param_name: str
        :return:
        :rtype: ParamSpec
        """
        return self.parameters[param_name][1]

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

    def get_random_parameters(self, serialize=False):
        """
        Initializes all parameters with their `get_random_value()` method
        and returns the dictionary representing that.
        :param serialize:
        :type serialize: bool
        :return:
        :rtype: dict|list
        """
        params = {}
        for name, (_, spec) in self.parameters.items():
            params[name] = spec.get_random_value()

        return self.serialize_params(params) if serialize else params


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

    def __init__(self, layers=None, params=None):
        """

        :param layers: Allowed layers for this neuron, should be a tuple or
                       set with the "input"/"output"/"hidden" strings. Defaults
                       to ("output", "hidden"), meaning you need to explicitly
                       specify input layer neuron types.
        :type layers: tuple[str]|list[str]
        :param params:
        :type params: list[ParamSpec|str]
        :return:
        """
        super(NeuronSpec, self).__init__(params=params)
        self.layers = ("output", "hidden") if layers is None else layers
