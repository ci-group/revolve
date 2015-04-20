import unittest
from ..convert import yaml_to_protobuf
from ..convert import RobotSpecificationException as SpecErr
from ..implementation import SpecImplementation, Part, Neuron

# Define YAML for test cases here
# Body
test_missing_body = """\
---
brain: {}
""".split("\n")

test_missing_part_id = '''\
---
body:
  type: "CoreComponent"
'''.split("\n")

test_missing_part_type = '''\
---
body:
  id: Core
'''.split("\n")

test_part_not_in_spec = '''\
---
body:
  id: Core
  type: NotExist
'''.split("\n")

test_arity_fail = '''\
---
body:
  id: Core
  type: CoreComponent
  children:
    2:
      id: "Sub1"
      type: "2Params"
'''.split("\n")

test_slot_reuse = '''\
---
body:
  id: Core
  type: CoreComponent
  children:
    0:
      id: Sub1
      type: 2Params
      children:
        0:
          id: SubSub1
          type: 2Params
'''.split("\n")

test_duplicate_part_id = '''\
---
body:
  id: Core
  type: CoreComponent
  children:
    0:
      id: Core
      type: 2Params
'''.split("\n")

# Brain
test_unknown_neuron_type = '''\
---
body:
  id: "Core"
  type: "CoreComponent"
brain:
  neurons:
    MyNeuron:
      type: Invalid
'''.split("\n")

test_duplicate_neuron_id = '''\
---
body:
  id: "Core"
  type: "CoreComponent"
brain:
  neurons:
    Core-out-0:
      type: Invalid
'''.split("\n")

test_unknown_param_neuron = '''\
---
body:
  id: "Core"
  type: "CoreComponent"
brain:
  params:
    SomeNeuron:
        type: Oscillator
        amplitude: 0.0
'''.split("\n")

test_input_destination_neuron = '''\
---
body:
  id: "Core"
  type: "CoreComponent"
brain:
  connections:
    - src: Core-in-0
      dst: Core-in-1
'''.split("\n")

test_input_params = '''\
---
body:
  id: "Core"
  type: "CoreComponent"
brain:
  params:
    Core-in-0:
        type: Oscillator
'''.split("\n")
# End of YAML for test cases

# Use this imaginary specification for all the tests
spec = SpecImplementation(
    parts={
        ("CoreComponent", "E"): Part(
            arity=2,
            output_neurons=1,
            input_neurons=2
        ),
        "2Params": Part(
            arity=2,
            input_neurons=2,
            output_neurons=2,
            params=["param_a", "param_b"],
            defaults={"param_a": -1, "param_b": 15}
        )
    },

    neurons={
        "Oscillator": Neuron(
            params=["period", "phaseOffset", "amplitude"]
        )
    }
)


class TestConvert(unittest.TestCase):
    """
    Tests a wide range of error cases for the
    YAML converter.
    """
    def test_simple_body_exceptions(self):
        """
        Tests some body part exceptions
        :return:
        """
        with self.assertRaisesRegexp(SpecErr, 'body'):
            yaml_to_protobuf(spec, test_missing_body)

        with self.assertRaisesRegexp(SpecErr, 'ID'):
            yaml_to_protobuf(spec, test_missing_part_id)

        with self.assertRaisesRegexp(SpecErr, 'type'):
            yaml_to_protobuf(spec, test_missing_part_type)

        with self.assertRaisesRegexp(SpecErr, 'spec'):
            yaml_to_protobuf(spec, test_part_not_in_spec)

        with self.assertRaisesRegexp(SpecErr, 'arity'):
            yaml_to_protobuf(spec, test_arity_fail)

        with self.assertRaisesRegexp(SpecErr, 'attached'):
            yaml_to_protobuf(spec, test_slot_reuse)

        with self.assertRaisesRegexp(SpecErr, 'Duplicate'):
            yaml_to_protobuf(spec, test_duplicate_part_id)

    def test_simple_brain_exceptions(self):
        """
        Tests some brain exceptions
        :return:
        """
        with self.assertRaisesRegexp(SpecErr, 'Unknown'):
            yaml_to_protobuf(spec, test_unknown_neuron_type)

        with self.assertRaisesRegexp(SpecErr, 'Duplicate'):
            yaml_to_protobuf(spec, test_duplicate_neuron_id)

        with self.assertRaisesRegexp(SpecErr, 'unknown'):
            yaml_to_protobuf(spec, test_unknown_param_neuron)

        with self.assertRaisesRegexp(SpecErr, 'input'):
            yaml_to_protobuf(spec, test_input_destination_neuron)

        with self.assertRaisesRegexp(SpecErr, 'Simple'):
            yaml_to_protobuf(spec, test_input_params)

    def test_working_body(self):
        """
        Tests a simple working body with various aspects
        :return:
        """
        # TODO Implement


if __name__ == '__main__':
    unittest.main()