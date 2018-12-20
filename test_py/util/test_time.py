from __future__ import absolute_import

import unittest

from pyrevolve.util import Time


class TestTime(unittest.TestCase):
    """
    Tests the time class
    """

    def test_create(self):
        a = Time(0, -10)
        self.assertEqual(a.sec, -1)
        self.assertEqual(a.nsec, 10e9 - 10)

    def test_float(self):
        a = Time(1, 5 * 10e8)
        self.assertAlmostEqual(1.5, float(a))

    def test_add(self):
        a = Time(5, 5*10e8)
        b = a + a
        self.assertEqual(b.sec, 11)
        self.assertEqual(b.nsec, 0)

        b = a + 1.1
        self.assertEqual(b.sec, 6)
        self.assertEqual(b.nsec, 6 * 10e8)

        b = 1.1 + a
        self.assertEqual(b.sec, 6)
        self.assertEqual(b.nsec, 6 * 10e8)

        a += a
        self.assertEqual(a.sec, 11)
        self.assertEqual(a.nsec, 0)

        a += 1.1
        self.assertEqual(a.sec, 12)
        self.assertEqual(a.nsec, 10e8)

    def test_subtract(self):
        a = Time(5, 5*10e8)
        b = a - Time(4, 6 * 10e8)
        self.assertEqual(b.sec, 0)
        self.assertEqual(b.nsec, 9*10e8)

        b = a - 1.1
        self.assertEqual(b.sec, 4)
        self.assertEqual(b.nsec, 4*10e8)

        b = 9.9 - a
        self.assertEqual(b.sec, 4)
        self.assertEqual(b.nsec, 4*10e8)

        a -= a
        self.assertEqual(a.sec, 0)
        self.assertEqual(a.nsec, 0)

        a -= Time(2, 10e8)
        self.assertEqual(a.sec, -3)
        self.assertEqual(a.nsec, 9*10e8)

        a += 1.1
        self.assertEqual(a.sec, -1)
        self.assertEqual(a.nsec, 0)

    def test_eq(self):
        a = Time(5, 5*10e8)
        self.assertEqual(a, 5.5)
        self.assertEqual(a, Time(5, 5*10e8))
        self.assertNotEqual(a, Time(5, 6*10e8))

    def test_cmp(self):
        a = Time(dbl=1.0)
        b = Time(dbl=2.0)
        c = Time(dbl=1.0)

        self.assertTrue(a < b)
        self.assertFalse(a > b)
        self.assertTrue(b > a)
        self.assertFalse(b < a)
        self.assertTrue(b >= a)
        self.assertFalse(b <= a)
        self.assertTrue(a <= b)
        self.assertFalse(a >= b)

        self.assertTrue(a <= c)
        self.assertTrue(a >= c)
        self.assertTrue(c >= a)
        self.assertTrue(a >= c)


