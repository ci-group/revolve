import unittest
from ...spec import SpecImplementation, PartSpec, NeuronSpec, Robot, BodyPart
from ...spec import RobotSpecificationException as SpecError
from ...spec.validation import validate_robot

# Imaginary specification for the tests
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
    p1.value = 0
    p2.value = 0
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

        with self.assertRaisesRegexp(SpecError, "part type"):
            validate_robot(spec, robot)

        # Make type valid, add invalid connection
        root.type = "CoreComponent"
        conn1 = root.child.add()
        conn1.src = -1
        conn1.dst = 5

        with self.assertRaisesRegexp(SpecError, "source slot"):
            validate_robot(spec, robot)

        conn1.src = 2
        with self.assertRaisesRegexp(SpecError, "source slot"):
            validate_robot(spec, robot)

        conn1.src = 1
        part1 = conn1.part
        part1.id = "Core"
        part1.type = "2Params"
        part1.orientation = 0

        with self.assertRaisesRegexp(SpecError, "Duplicate"):
            validate_robot(spec, robot)

        # Make the ID valid, connection dst slot is not
        part1.id = "Part1"
        with self.assertRaisesRegexp(SpecError, "destination slot"):
            validate_robot(spec, robot)

        conn1.dst = 0

        # Parameter count is now wrong
        with self.assertRaisesRegexp(SpecError, "parameters"):
            validate_robot(spec, robot)

        p1 = part1.param.add()
        p2 = part1.param.add()
        p1.value = 0
        p2.value = 0

        # Add a child at slot connected to parent
        part1conn = part1.child.add()
        part1conn.part.CopyFrom(_get_simple_part("Part1Nest1"))
        part1conn.src = 0
        part1conn.dst = 1

        with self.assertRaisesRegexp(SpecError, "occupied"):
            validate_robot(spec, robot)

        part1conn.src = 1

        part1conn2 = part1.child.add()
        part1conn2.part.CopyFrom(_get_simple_part("Part1Nest1"))
        part1conn2.src = 1
        part1conn2.dst = 0

        with self.assertRaisesRegexp(SpecError, "occupied"):
            validate_robot(spec, robot)

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
        conn.src = 0
        conn.dst = 0
        conn.part.CopyFrom(_get_simple_part("Part1"))

        # The first error we'll get is we're missing
        # expected neurons.
        with self.assertRaisesRegexp(SpecError, "expected"):
            validate_robot(spec, robot)

        n = [brain.neuron.add() for _ in range(7)]
        for neur in n:
            neur.type = 'Simple'
            neur.param.add()
            neur.param[0].value = 0

        n[0].id, n[0].layer = "Core-out-0", "input"
        n[1].id, n[1].layer = "Core-in-0", "input"
        n[2].id, n[2].layer = "Core-in-1", "input"

        n[3].id, n[3].layer = "Part1-in-0", "input"
        n[4].id, n[4].layer = "Part1-in-1", "input"
        n[5].id, n[5].layer = "Part1-out-0", "output"
        n[6].id, n[6].layer = "Part1-out-1", "output"

        # Layer of Core-out-0 neuron is incorrect
        with self.assertRaisesRegexp(SpecError, "should be in layer"):
            validate_robot(spec, robot)

        n[0].layer = "output"

        # Core-out-0 neuron should be assigned to a part
        with self.assertRaisesRegexp(SpecError, "should have a part"):
            validate_robot(spec, robot)

        n[0].partId = "Fake"

        # Non-existing part ID
        with self.assertRaisesRegexp(SpecError, "Unknown part"):
            validate_robot(spec, robot)

        n[0].partId = n[1].partId = n[2].partId = "Core"
        n[3].partId = n[4].partId = n[5].partId = n[6].partId = "Part1"

        # Input neuron should be "Simple"
        n[1].type = "Oscillator"
        with self.assertRaisesRegexp(SpecError, "Simple"):
            validate_robot(spec, robot)

        n[1].type = "Simple"

        # Add hidden neuron with duplicate ID
        hidden = brain.neuron.add()
        hidden.id, hidden.layer = "Core-out-0", "hidden"

        with self.assertRaisesRegexp(SpecError, "Duplicate"):
            validate_robot(spec, robot)

        hidden.type = "Fake"
        hidden.param.add()
        hidden.id = "hidden"

        with self.assertRaisesRegexp(SpecError, "Unspecified"):
            validate_robot(spec, robot)

        hidden.type = "Oscillator"

        # Wrong number of parameters for oscillator
        with self.assertRaisesRegexp(SpecError, "parameters"):
            validate_robot(spec, robot)

        hidden.param.add()
        hidden.param.add()
        hidden.param[0].value = hidden.param[1].value = hidden.param[2].value = 0

        # This should be fine now, do nothing to assert it doesn't raise
        validate_robot(spec, robot)

        # Test some connections
        a = brain.connection.add()
        a.src = "hidden"
        a.dst = "Part1-in-0"

        # Wrong number of parameters for oscillator
        with self.assertRaisesRegexp(SpecError, "input"):
            validate_robot(spec, robot)

        a.dst = "Part1-out-1"

        # Create duplicate connection
        b = brain.connection.add()
        b.src = "hidden"
        b.dst = "Part1-out-1"

        with self.assertRaisesRegexp(SpecError, "Duplicate"):
            validate_robot(spec, robot)

        b.dst = "Part1-out-0"

        # Again, this should be fine
        validate_robot(spec, robot)

if __name__ == '__main__':
    unittest.main()