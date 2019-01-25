from __future__ import absolute_import

import unittest

from pyrevolve.spec import BodyImplementation, NeuralNetImplementation, PartSpec, NeuronSpec, ParamSpec, Robot, BodyPart
from pyrevolve.spec import RobotSpecificationException as SpecError, RobotValidator

# Imaginary specification for the tests
body_spec = BodyImplementation(
    {
        ("CoreComponent", "E"): PartSpec(
            arity=2,
            outputs=1,
            inputs=2
        ),
        "2Params": PartSpec(
            arity=2,
            inputs=2,
            outputs=2,
            params=[ParamSpec("param_a", default=-1, min_value=-2, max_value=0, max_inclusive=False),
                    ParamSpec("param_b", default=15)]
        )
    }
)

brain_spec = NeuralNetImplementation(
    {
        "Simple": NeuronSpec(params=["bias"]),
        "Oscillator": NeuronSpec(
            params=["period", "phaseOffset", "amplitude"]
        )
    }
)


def validate_robot(robot):
    """
    :param robot:
    :return:
    """
    validator = RobotValidator(robot, body_spec, brain_spec)
    validator.validate()


def _get_simple_part(part_id):
    """
    Helper function to get a simple valid 2Params
    part.
    :return:
    """
    part = BodyPart()
    part.id = part_id
    p1 = part.param.add()
    p2 = part.param.add()
    p1.value = -0.5
    p2.value = -0.5
    part.type = "2Params"
    return part


class TestValidate(unittest.TestCase):
    """
    Tests the spec validator
    """

    def test_body_errors(self):
        """
        Tests a bunch of body / body connection errors.
        :return:
        """
        # Check invalid type
        robot = Robot()
        root = robot.body.root
        root.id = "Core"
        root.type = "InvalidType"

        with self.assertRaisesRegex(SpecError, "part type"):
            validate_robot(robot)

        # Make type valid, add invalid connection
        root.type = "CoreComponent"
        conn1 = root.child.add()
        conn1.src_slot = -1
        conn1.dst_slot = 5

        with self.assertRaisesRegex(SpecError, "source slot"):
            validate_robot(robot)

        conn1.src_slot = 2
        with self.assertRaisesRegex(SpecError, "source slot"):
            validate_robot(robot)

        conn1.src_slot = 1
        part1 = conn1.part
        part1.id = "Core"
        part1.type = "2Params"
        part1.orientation = 0

        with self.assertRaisesRegex(SpecError, "Duplicate"):
            validate_robot(robot)

        # Make the ID valid, connection dst slot is not
        part1.id = "Part1"
        with self.assertRaisesRegex(SpecError, "destination slot"):
            validate_robot(robot)

        conn1.dst_slot = 0

        # Parameter count is now wrong
        with self.assertRaisesRegex(SpecError, "parameters"):
            validate_robot(robot)

        p1 = part1.param.add()
        p2 = part1.param.add()
        p1.value = 0
        p2.value = 0

        # Parameter count correct, but the parameters are just out of range
        with self.assertRaisesRegex(SpecError, "range"):
            validate_robot(robot)

        p1.value = -0.5
        p2.value = -0.5

        # Add a child at slot connected to parent
        part1conn = part1.child.add()
        part1conn.part.CopyFrom(_get_simple_part("Part1Nest1"))
        part1conn.src_slot = 0
        part1conn.dst_slot = 1

        with self.assertRaisesRegex(SpecError, "occupied"):
            validate_robot(robot)

        part1conn.src_slot = 1

        part1conn2 = part1.child.add()
        part1conn2.part.CopyFrom(_get_simple_part("Part1Nest1"))
        part1conn2.src_slot = 1
        part1conn2.dst_slot = 0

        with self.assertRaisesRegex(SpecError, "occupied"):
            validate_robot(robot)

    def test_brain_errors(self):
        """
        Tests various brain errors
        :return:
        """
        # Create a simple robot with one root and one child
        robot = Robot()
        brain = robot.brain
        root = robot.body.root
        root.id = "Core"
        root.type = "CoreComponent"

        conn = root.child.add()
        conn.src_slot = 0
        conn.dst_slot = 0
        conn.part.CopyFrom(_get_simple_part("Part1"))

        # The first error we'll get is we're missing
        # expected neurons.
        with self.assertRaisesRegex(SpecError, "expected"):
            validate_robot(robot)

        # Add a bunch of input and output neurons
        n = [brain.neuron.add() for _ in range(7)]
        n[0].id, n[0].layer = "Core-out-0", "output"
        n[1].id, n[1].layer = "Core-in-0", "input"
        n[2].id, n[2].layer = "Core-in-1", "input"

        n[3].id, n[3].layer = "Part1-in-0", "input"
        n[4].id, n[4].layer = "Part1-in-1", "input"
        n[5].id, n[5].layer = "Part1-out-0", "output"
        n[6].id, n[6].layer = "Part1-out-1", "output"

        for neur in n:
            neur.type = 'Simple' if neur.layer == "output" else "Input"

            if neur.type == 'Simple':
                neur.param.add()
                neur.param[0].value = 0

        # Layer of Core-out-0 neuron is incorrect
        n[0].layer = "input"
        with self.assertRaisesRegex(SpecError, "should be in layer"):
            validate_robot(robot)

        n[0].layer = "output"

        # Core-out-0 neuron should be assigned to a part
        with self.assertRaisesRegex(SpecError, "should have a part"):
            validate_robot(robot)

        n[0].partId = "Fake"

        # Non-existing part ID
        with self.assertRaisesRegex(SpecError, "Unknown part"):
            validate_robot(robot)

        n[0].partId = n[1].partId = n[2].partId = "Core"
        n[3].partId = n[4].partId = n[5].partId = n[6].partId = "Part1"

        # Input neuron should be "Input"
        n[1].type = "Oscillator"
        with self.assertRaisesRegex(SpecError, "layer 'input'"):
            validate_robot(robot)

        n[1].type = "Input"

        # Add hidden neuron with duplicate ID
        hidden = brain.neuron.add()
        hidden.id, hidden.layer = "Core-out-0", "hidden"

        with self.assertRaisesRegex(SpecError, "Duplicate"):
            validate_robot(robot)

        hidden.type = "Fake"
        hidden.param.add()
        hidden.id = "hidden"

        with self.assertRaisesRegex(SpecError, "Unspecified"):
            validate_robot(robot)

        hidden.type = "Oscillator"

        # Wrong number of parameters for oscillator
        with self.assertRaisesRegex(SpecError, "parameters"):
            validate_robot(robot)

        hidden.param.add()
        hidden.param.add()
        hidden.param[0].value = hidden.param[1].value = hidden.param[2].value = 0

        # This should be fine now, do nothing to assert it doesn't raise
        validate_robot(robot)

        # Test some connections
        a = brain.connection.add()
        a.src_slot = "hidden"
        a.dst_slot = "Part1-in-0"

        # Wrong number of parameters for oscillator
        with self.assertRaisesRegex(SpecError, "input"):
            validate_robot(robot)

        a.dst_slot = "Part1-out-1"

        # Create duplicate connection
        b = brain.connection.add()
        b.src_slot = "hidden"
        b.dst_slot = "Part1-out-1"

        with self.assertRaisesRegex(SpecError, "Duplicate"):
            validate_robot(robot)

        b.dst_slot = "Part1-out-0"

        # Again, this should be fine
        validate_robot(robot)


if __name__ == '__main__':
    unittest.main()
