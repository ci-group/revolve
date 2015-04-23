import unittest
from ...convert import yaml_to_protobuf
from ...spec import SpecImplementation, PartSpec, NeuronSpec, RobotSpecificationException as SpecErr

# Define YAML for test cases here
# Body
test_missing_body = """\
---
brain: {}
"""

test_missing_part_id = '''\
---
body:
  type: "CoreComponent"
'''

test_missing_part_type = '''\
---
body:
  id: Core
'''

test_part_not_in_spec = '''\
---
body:
  id: Core
  type: NotExist
'''

test_arity_fail = '''\
---
body:
  id: Core
  type: CoreComponent
  children:
    2:
      id: "Sub1"
      type: "2Params"
'''

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
'''

test_duplicate_part_id = '''\
---
body:
  id: Core
  type: CoreComponent
  children:
    0:
      id: Core
      type: 2Params
'''

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
'''

test_duplicate_neuron_id = '''\
---
body:
  id: "Core"
  type: "CoreComponent"
brain:
  neurons:
    Core-out-0:
      type: Invalid
'''

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
'''

test_input_destination_neuron = '''\
---
body:
  id: "Core"
  type: "CoreComponent"
brain:
  connections:
    - src: Core-in-0
      dst: Core-in-1
'''

test_input_params = '''\
---
body:
  id: "Core"
  type: "CoreComponent"
brain:
  params:
    Core-in-0:
        type: Oscillator
'''

# Full
test_simple_robot = '''\
---
body:
  id: Core
  type: CoreComponent
  children:
    0:
      id: Sub1
      type: 2Params
      orientation: 180
      slot: 1
    1:
      id: Sub2
      type: 2Params
      params:
        param_a: 10
        param_b: 20
brain:
  neurons:
    Hidden1:
      type: Oscillator
      period: 0.1
      phaseOffset: 0.2
      amplitude: 0.3
    Hidden2:
      type: Oscillator
    Hidden3: {}
  params:
    Sub1-out-1:
      type: Oscillator
      phaseOffset: 10
    Sub2-out-0:
      type: Oscillator
  connections:
    - src: Sub1-out-1
      dst: Sub1-out-1
      weight: 2
    - src: Sub2-in-1
      dst: Sub1-out-1
'''

# End of YAML for test cases

# Use this imaginary specification for all the tests
spec = SpecImplementation(
    parts={
        ("CoreComponent", "E"): PartSpec(
            arity=2,
            output_neurons=1,
            input_neurons=2
        ),
        "2Params": PartSpec(
            arity=2,
            input_neurons=2,
            output_neurons=2,
            params=["param_a", "param_b"],
            defaults={"param_a": -1, "param_b": 15}
        )
    },

    neurons={
        "Oscillator": NeuronSpec(
            params=["period", "phaseOffset", "amplitude"]
        )
    }
)


class TestConvertYaml(unittest.TestCase):
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

    def test_simple_robot(self):
        """
        Tests whether a simple robot is correctly serialized.
        :return:
        """
        robot = yaml_to_protobuf(spec, test_simple_robot)

        # Make sure all required fields are set
        self.assertTrue(robot.IsInitialized())

        self.assertEquals(0, robot.id, "Robot ID not correctly set.")

        root = robot.body.root
        self.assertEquals("Core", root.id, "Root ID not correctly set. (%s)" % root.id)

        self.assertEquals(2, len(root.child), "Root should have two children.")

        sub1_conn = root.child[0]
        sub2_conn = root.child[1]

        # Check connection sources / destinations
        self.assertEquals(0, sub1_conn.src)
        self.assertEquals(1, sub2_conn.src)
        self.assertEquals(1, sub1_conn.dst)
        self.assertEquals(0, sub2_conn.dst)

        sub1 = sub1_conn.part
        sub2 = sub2_conn.part

        # Check types
        self.assertEquals("2Params", sub1.type)
        self.assertEquals("2Params", sub2.type)

        # Check parameter lists
        sub1params = [p.value for p in sub1.param]
        sub2params = [p.value for p in sub2.param]

        self.assertEquals([-1, 15], sub1params)
        self.assertEquals([10, 20], sub2params)

        # Check the brain
        brain = robot.brain

        # 1 + 2 + 2 output, 2 + 2 + 2 input, 3 hidden
        self.assertEquals(14, len(brain.neuron))
        self.assertEquals(len(brain.connection), 2)

        conn0 = brain.connection[0]
        self.assertEquals("Sub1-out-1", conn0.src)
        self.assertEquals("Sub1-out-1", conn0.dst)
        self.assertEquals(2, conn0.weight)

        conn1 = brain.connection[1]
        self.assertEquals("Sub2-in-1", conn1.src)
        self.assertEquals("Sub1-out-1", conn1.dst)
        self.assertEquals(0, conn1.weight)

        hidden1 = [a for a in brain.neuron if a.id == "Hidden1"][0]
        hidden1params = [p.value for p in hidden1.param]
        self.assertEquals([0.1, 0.2, 0.3], hidden1params)

        hidden2 = [a for a in brain.neuron if a.id == "Hidden2"][0]
        hidden2params = [p.value for p in hidden2.param]
        self.assertEquals([0, 0, 0], hidden2params)

        hidden3 = [a for a in brain.neuron if a.id == "Hidden3"][0]
        self.assertEquals("Simple", hidden3.type)

        sub1 = [a for a in brain.neuron if a.id == "Sub1-out-1"][0]
        sub1params = [p.value for p in sub1.param]
        self.assertEquals([0, 10, 0], sub1params)

if __name__ == '__main__':
    unittest.main()