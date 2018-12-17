"""
Tests the `BodyEncoder` and the `NeuralNetworkEncoder` using a little help from
the YAML converter to create the basic protobuf message.
"""
from __future__ import absolute_import

import unittest

from pyrevolve.convert import yaml_to_robot, robot_to_yaml
from pyrevolve.spec import PartSpec, NeuronSpec, ParamSpec, RobotSpecificationException as SpecErr
from pyrevolve.spec import BodyImplementation, NeuralNetImplementation
import yaml


# the basic yaml object that will be altered for the diffent test cases
basic_yaml_object = '''\
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
      children:
        0:
          id          : UpperLeg2
          type        : 2Params
          orientation : 90
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
# the body and brain specifications
body_spec = BodyImplementation({
    ("CoreComponent", "E"): PartSpec(
        arity=2,
        outputs=1,
        inputs=2
    ),
    "2Params": PartSpec(
        arity=2,
        inputs=2,
        outputs=2,
        params=[ParamSpec("param_a", default=-1), ParamSpec("param_b", default=15)]
    )
})

brain_spec = NeuralNetImplementation({
    "Simple": NeuronSpec(params=["bias"]),
    "Oscillator": NeuronSpec(
        params=["period", "phaseOffset", "amplitude"]
    )
})


# Enter the test cases below (make alterations to the basic yaml object)
# Body test cases
missing_body = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
missing_body.body.root.Clear()

missing_id = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
missing_id.body.root.id = ""

missing_part_type = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
missing_part_type.body.root.type = ""

part_not_in_spec = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
part_not_in_spec.body.root.type = "NonExistent"

arity_fail = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
arity_fail.body.root.child[0].src = 5

slot_reuse = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
slot_reuse.body.root.child[0].part.child[0].src = 1

duplicate_part_id = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
duplicate_part_id.body.root.child[0].part.id = "Core"

# Brain test cases
unknown_neuron_type = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
unknown_neuron_type.brain.neuron[1].type = "invalid"

duplicate_neuron_id = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
duplicate_neuron_id.brain.neuron[0].id = "thesame"
duplicate_neuron_id.brain.neuron[1].id = "thesame"

input_destination_neuron = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
input_destination_neuron.brain.neuron[1].type = "invalid"


# convenience wrapper
def rty(protobuf):
    return robot_to_yaml(body_spec, brain_spec, protobuf)


class TestConvertYaml(unittest.TestCase):
    """
    Tests error cases for the converter
    """
    def test_simple_body_exceptions(self):
        with self.assertRaises(SpecErr):
            rty(missing_body)

        with self.assertRaises(SpecErr):
            rty(missing_id)

        with self.assertRaises(SpecErr):
            rty(missing_part_type)

        with self.assertRaises(SpecErr):
            rty(part_not_in_spec)

        with self.assertRaises(SpecErr):
            rty(arity_fail)

        with self.assertRaises(SpecErr):
            rty(slot_reuse)

        with self.assertRaises(SpecErr):
            rty(duplicate_part_id)

    def test_simple_brain_exceptions(self):
        """
        Tests some brain exceptions
        :return:
        """
        with self.assertRaises(SpecErr):
            rty(unknown_neuron_type)

        with self.assertRaises(SpecErr):
            rty(duplicate_neuron_id)

    def test_simple_robot(self):
        """
        Tests whether a simple robot is correctly encoded.
        :return:
        """

        protobuf_robot = yaml_to_robot(body_spec, brain_spec, basic_yaml_object)
        yaml_robot = rty(protobuf_robot)
        robot = yaml.load(yaml_robot)

        self.assertEquals(0, robot["id"], "Robot ID not correctly set.")

        self.assertEquals("Core", robot["body"]["id"], "Root ID not correctly set. (%s)" % robot["body"]["id"])

        self.assertEquals(2, len(robot["body"]["children"]), "Root should have two children.")

if __name__ == '__main__':
    unittest.main()
