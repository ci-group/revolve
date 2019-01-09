"""
Tests a relatively complex align feature
"""
from __future__ import absolute_import
import unittest
from sdfbuilder import Link
from sdfbuilder.math import Vector3
from math import pi, sqrt


class TestPosable(unittest.TestCase):
    """
    Tests various aspects of the Posable class, such as
    alignment and rotation.
    """
    def test_direction_conversion(self):
        """
        Tests converting vectors between direction frames.
        :return:
        """
        link = Link("my_link")
        point = Vector3(0, 0, 1)

        # At this point, it should be the same in the
        # parent direction
        x, y, z = link.to_parent_direction(point)
        self.assertAlmostEqual(x, point.x)
        self.assertAlmostEqual(y, point.y)
        self.assertAlmostEqual(z, point.z)

        # Now rotate the link 90 degrees over (1, 1, 0),
        # this should cause the local vector (0, 1, 1)
        # to land at 0.5 * [sqrt(2), -sqrt(2), 0]
        link.rotate_around(Vector3(1, 1, 0), 0.5 * pi, relative_to_child=False)
        hs2 = 0.5 * sqrt(2)
        x, y, z = link.to_parent_direction(point)
        self.assertAlmostEqual(x, hs2)
        self.assertAlmostEqual(y, -hs2)
        self.assertAlmostEqual(z, 0)

    def test_complex_align(self):
        """
        Create a structure with some complicated rotation /
        align transformations and tests the resulting positions.
        :return:
        """
        from sdfbuilder.examples.complex_align import link, minibox, link2

        # Now, the asserts. These positions have been verified through
        # visual inspection and then copied from the SDF - we might thus
        # say this functions as a regression test.

        # First, the position of the first link.
        roll, pitch, yaw = link.get_rotation().get_rpy()
        x, y, z = link.get_position()
        self.assertAlmostEqual(x, 2.776709, msg="Incorrect x position.")
        self.assertAlmostEqual(y, -0.1100423, msg="Incorrect y position.")
        self.assertAlmostEqual(z, 2.8333333, msg="Incorrect z position.")
        self.assertAlmostEqual(roll, 1.8325957145940461, msg="Incorrect roll.")
        self.assertAlmostEqual(pitch, 0.3398369, msg="Incorrect pitch.")
        self.assertAlmostEqual(yaw, 2.8797932657906435, msg="Incorrect yaw.")

        # Now, position of the minibox
        roll, pitch, yaw = minibox.get_rotation().get_rpy()
        x, y, z = minibox.get_position()
        self.assertAlmostEqual(x, 4.655811238272279, msg="Incorrect x position.")
        self.assertAlmostEqual(y, 1.291709623134523, msg="Incorrect y position.")
        self.assertAlmostEqual(z, 1.7256842193500852, msg="Incorrect z position.")
        self.assertAlmostEqual(roll, -2.1377528428632186, msg="Incorrect roll.")
        self.assertAlmostEqual(pitch, -0.6933926357494202, msg="Incorrect pitch.")
        self.assertAlmostEqual(yaw, 1.0364317772632718, msg="Incorrect yaw.")

        # Finally, position of link2
        roll, pitch, yaw = link2.get_rotation().get_rpy()
        x, y, z = link2.get_position()
        self.assertAlmostEqual(x, 0.5, msg="Incorrect x position.")
        self.assertAlmostEqual(y, 0.5, msg="Incorrect y position.")
        self.assertAlmostEqual(z, 2, msg="Incorrect z position.")
        self.assertAlmostEqual(roll, 1.2199169159226388, msg="Incorrect roll.")
        self.assertAlmostEqual(pitch, 0.24650585550379217, msg="Incorrect pitch.")
        self.assertAlmostEqual(yaw, 1.2199169159226388, msg="Incorrect yaw.")

if __name__ == '__main__':
    unittest.main()
