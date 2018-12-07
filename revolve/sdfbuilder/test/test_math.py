"""
Math tests, this clearly needs more stuff.
"""
import unittest
from sdfbuilder.math import Quaternion


class TestMath(unittest.TestCase):
    """
    Tests the math components
    """

    def test_euler_angles(self):
        """
        Tests Euler angles from a quaternion that used to fail. Other Euler
        angles are tested from visual inspection in the `posable` test case.
        :return:
        """
        q = Quaternion(-0.5, 0.5, 0.5, 0.5)
        roll, pitch, yaw = q.get_rpy()
        self.assertAlmostEquals(-1.5707963267948968, roll, msg="Invalid roll.")
        self.assertAlmostEquals(-1.5707963267948968, pitch, msg="Invalid roll.")
        self.assertAlmostEquals(0, yaw, msg="Invalid yaw")


if __name__ == '__main__':
    unittest.main()
