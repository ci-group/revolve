import random
import unittest

from revolve.generate import BodyGenerator
from revolve.spec import BodyImplementation, \
                         NormalDistParamSpec, \
                         ParamSpec, \
                         PartSpec

# Some imaginary body specification
body_spec = BodyImplementation(
        {
            "Core"    : PartSpec(
                    arity=2,
                    outputs=2,
                    inputs=2
            ),
            "2Params" : PartSpec(
                    arity=2,
                    inputs=2,
                    outputs=2,
                    params=[ParamSpec("param_a", default=-1, min_value=-2,
                                      max_value=0, max_inclusive=False),
                            NormalDistParamSpec("param_b", mean=15, stddev=5,
                                                default=15)]
            ),
            "SomePart": PartSpec(arity=1, inputs=3, outputs=3)
        }
)


# Simple function to count the number of parts in a body
def _count_parts(root):
    count = len(root.child)
    for child in root.child:
        count += _count_parts(child.part)

    return count


class TestBodyGenerator(unittest.TestCase):
    """
    Some simple tests regarding body generation
    """

    def test_constraints(self):
        """
        In this test, we build a body generator with a maximum
        number of inputs / outputs that is already satisfied
        by the root component, and ensure no further generation
        is done.

        :return:
        """
        # Seed so we can reproduce if this goes wrong
        seed = random.randint(0, 10000)
        random.seed(seed)

        gen = BodyGenerator(
                body_spec,
                root_parts=["Core"],
                attach_parts=["2Params"],
                max_inputs=2,
                max_outputs=10,
                max_parts=100,
                fix_num_parts=True
        )

        body = gen.generate()
        self.assertEquals("Core", body.root.type,
                          "Root type should be 'Core' (seed %d)." % seed)
        self.assertEquals(0, len(body.root.child),
                          "Too many inputs were generated (seed %d)." % seed)

        gen.max_inputs = 100
        gen.max_outputs = 2

        body = gen.generate()
        self.assertEquals(0, len(body.root.child),
                          "Too many outputs were generated (seed %d)." % seed)

        # This leaves enough room for a 2Params child, but not enough for a SomePart child
        gen.max_outputs = 4
        body = gen.generate()
        self.assertEquals(_count_parts(body.root), 1,
                          "One child part should be present (seed %d)." % seed)
        self.assertEquals("2Params", body.root.child[0].part.type,
                          "Child part should be of type 2Params (seed %d)." % seed)

        gen.max_inputs = gen.max_outputs = 100
        gen.max_parts = 1
        body = gen.generate()
        self.assertEquals(0, _count_parts(body.root),
                          "No child parts should be present (seed %d)." % seed)

    def test_valid(self):
        """
        Generates a body and ensures it is completely initialized.
        :return:
        """
        # Seed so we can reproduce if this goes wrong
        seed = random.randint(0, 10000)
        random.seed(seed)

        gen = BodyGenerator(
                body_spec,
                root_parts=["Core"],
                attach_parts=["2Params"],
                max_inputs=100,
                max_outputs=100,
                max_parts=10,
                fix_num_parts=True
        )

        body = gen.generate()
        self.assertTrue(body.IsInitialized(),
                        "Incomplete body (seed %d)." % seed)
