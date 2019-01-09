from __future__ import absolute_import
import math
from sdfbuilder.math import Vector3
from sdfbuilder import Link
import unittest
from sdfbuilder.structure import Collision, Box


class TestLink(unittest.TestCase):
    def test_link_inertia(self):
        """
        A similar test to what is done in structure.py to test
        compound inertia, only now we do it in a link.
        :return:
        """
        # First, the comparison inertial
        total_mass = 100
        simple_box = Box(4, 8, 12, mass=total_mass)
        i1 = simple_box.get_inertial()

        # Same split as in structure.py test, only now
        # we're making sure it is distributed around the
        # origin since box inertial above is relative to
        # its center of mass
        link = Link("test_link")
        y_axis = Vector3(0, 1, 0)
        deg90 = 0.5 * math.pi

        # Split 5 / 7 in z-direction
        frac = total_mass / 12.0
        total_up = 5 * frac
        total_down = 7 * frac

        # We split the upper part 6 / 2 in the y-direction
        # and align in the center.
        frac_up = total_up / 8.0
        sub1 = Collision("sub1", geometry=Box(5, 6, 4, mass=6 * frac_up))
        sub1.rotate_around(y_axis, deg90)
        sub1.translate(Vector3(0, 1, 3.5))
        link.add_element(sub1)

        sub2 = Collision("sub2", geometry=Box(5, 2, 4, mass=2 * frac_up))
        sub2.rotate_around(y_axis, deg90)
        sub2.translate(Vector3(0, -3, 3.5))
        link.add_element(sub2)

        sub3 = Collision("sub3", geometry=Box(4, 8, 7, mass=total_down))
        sub3.translate(Vector3(0, 0, -2.5))
        link.add_element(sub3)

        link.calculate_inertial()
        self.assertEqualTensors(i1, link.inertial)

    def assertEqualTensors(self, i1, i2):
        self.assertAlmostEquals(i1.ixx, i2.ixx)
        self.assertAlmostEquals(i1.ixy, i2.ixy)
        self.assertAlmostEquals(i1.ixz, i2.ixz)
        self.assertAlmostEquals(i1.iyy, i2.iyy)
        self.assertAlmostEquals(i1.iyy, i2.iyy)

if __name__ == '__main__':
    unittest.main()
