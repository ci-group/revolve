from __future__ import absolute_import
import unittest
import math
from sdfbuilder.math import Vector3
from sdfbuilder.structure.geometries import Box, CompoundGeometry


class TestGeometry(unittest.TestCase):
    """
    Tests mostly the compound geometry
    """
    def test_box_inertia(self):
        """
        """
        x, y, z = 10, 20, 30
        mass = 250
        box = Box(x, y, z, mass=mass)
        inert = box.get_inertial()

        self.assertAlmostEquals(inert.ixx, mass * (y**2 + z**2) / 12.0)
        self.assertAlmostEquals(inert.iyy, mass * (x**2 + z**2) / 12.0)
        self.assertAlmostEquals(inert.izz, mass * (x**2 + y**2) / 12.0)
        self.assertAlmostEquals(inert.ixy, 0)
        self.assertAlmostEquals(inert.ixz, 0)
        self.assertAlmostEquals(inert.iyz, 0)

    def test_compound_center_mass(self):
        """
        Born from a numerical oddity in the compound inertial
        test; checks the center of mass for a compound geometry.
        """
        compound = CompoundGeometry()
        y_axis = Vector3(0, 1, 0)
        deg90 = 0.5 * math.pi

        frac_up = 57.5
        sub1 = Box(5, 6, 4, mass=6 * frac_up)
        sub1.rotate_around(y_axis, deg90)
        sub1.translate(Vector3(0, 1, 2.5))
        compound.add_geometry(sub1)

        sub2 = Box(5, 2, 4, mass=2 * frac_up)
        sub2.rotate_around(y_axis, deg90)
        sub2.translate(Vector3(0, -3, 2.5))
        compound.add_geometry(sub2)

        x, y, z = compound.get_center_of_mass()
        self.assertAlmostEquals(x, 0)
        self.assertAlmostEquals(y, 0)
        self.assertAlmostEquals(z, 2.5)

    def test_compound_inertia(self):
        """
        Performs a simple compound geometry inertia check
        by comparing two aligned boxes with one big box,
        with the same mass distribution and total mass.
        """
        total_mass = 100
        simple_box = Box(4, 8, 12, mass=total_mass)
        i1 = simple_box.get_inertial()

        # # First the most trivial case - two same size
        # # boxes with half the mass.
        compound = CompoundGeometry()
        sub1 = Box(4, 8, 12, mass=0.5 * total_mass)
        sub2 = Box(4, 8, 12, mass=0.5 * total_mass)
        compound.add_geometry(sub1)
        compound.add_geometry(sub2)
        i2 = compound.get_inertial()
        self.assertEqualTensors(i1, i2)

        # Next, we try to boxes positioned on top
        # of each other, with the mass divided over them.
        compound = CompoundGeometry()
        sub1 = Box(4, 8, 5, mass=total_mass * 5.0 / 12)
        sub2 = Box(4, 8, 7, mass=total_mass * 7.0 / 12)
        sub1.translate(Vector3(0, 0, 2.5))
        sub2.translate(Vector3(0, 0, -3.5))
        compound.add_geometry(sub1)
        compound.add_geometry(sub2)
        i2 = compound.get_inertial()
        self.assertEqualTensors(i1, i2)

        # Finally, something involving rotation, and different sizes.
        # Note that we get the inertia tensor relative to the compound's
        # center of mass, so it doesn't actually matter exactly how it's
        # aligned on the axes.
        compound = CompoundGeometry()
        y_axis = Vector3(0, 1, 0)
        deg90 = 0.5 * math.pi

        # Split 5 / 7 in z-direction
        frac = total_mass / 12.0
        total_up = 5 * frac
        total_down = 7 * frac

        # We split the upper part 6 / 2 in the y-direction
        # The alignment with the lower part in y *does* matter,
        # it should still be centered. We translate sub1
        # +1 so the total mass on the + side is 4,
        # and translate sub2 -3 to align with its left side.
        frac_up = total_up / 8.0
        sub1 = Box(5, 6, 4, mass=6 * frac_up)
        sub1.rotate_around(y_axis, deg90)
        sub1.translate(Vector3(0, 1, 2.5))
        compound.add_geometry(sub1)

        sub2 = Box(5, 2, 4, mass=2 * frac_up)
        sub2.rotate_around(y_axis, deg90)
        sub2.translate(Vector3(0, -3, 2.5))
        compound.add_geometry(sub2)

        sub3 = Box(4, 8, 7, mass=total_down)
        sub3.translate(Vector3(0, 0, -3.5))
        compound.add_geometry(sub3)

        i2 = compound.get_inertial()
        self.assertEqualTensors(i1, i2)

        # Let's try this same thing again, only combining
        # sub1 and sub2 in a nested compound geometry
        compound = CompoundGeometry()
        inner_compound = CompoundGeometry()

        inner_compound.add_geometry(sub1)
        inner_compound.add_geometry(sub2)

        compound.add_geometry(inner_compound)
        compound.add_geometry(sub3)

        i2 = compound.get_inertial()
        self.assertEqualTensors(i1, i2)

    def assertEqualTensors(self, i1, i2):
        self.assertAlmostEquals(i1.ixx, i2.ixx)
        self.assertAlmostEquals(i1.ixy, i2.ixy)
        self.assertAlmostEquals(i1.ixz, i2.ixz)
        self.assertAlmostEquals(i1.iyy, i2.iyy)
        self.assertAlmostEquals(i1.iyy, i2.iyy)

if __name__ == '__main__':
    unittest.main()
