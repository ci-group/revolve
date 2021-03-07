from __future__ import division

import numpy as np

from .transformations import quaternion_multiply
from .transformations import quaternion_matrix
from .transformations import quaternion_from_matrix
from .transformations import euler_from_quaternion
from .transformations import quaternion_about_axis
from .transformations import quaternion_conjugate
from .transformations import quaternion_inverse
from .transformations import quaternion_from_euler

# Epsilon value used for zero comparisons
EPSILON = 1e-5
OPPOSITE = -1
PARALLEL = 1
NOT_PARALLEL = 0


class VectorBase(object):
    """
    Base class with shared functionality for Quaternion / Vector3
    """
    LENGTH = 0
    """ Required length of the vector """

    ATTRS = ''
    """ Indexed attributes to be retrieved by __getattr__ """

    def __init__(self, *args):
        """

        :param args:
        :return:
        """
        if len(args) == 1 and hasattr(args[0], '__iter__'):
            self.data = np.array(args[0], dtype=np.float_, copy=True)
        else:
            self.data = np.array(args, dtype=np.float_, copy=True)

        if len(self.data) != self.LENGTH:
            raise AssertionError("Invalid data size {}, expecting {}".format(
                    len(self.data),
                    self.LENGTH))

    def __copy__(self):
        """
        Creates a copy of the vector class
        :return:
        """
        return self.__class__(self.data)

    copy = __copy__

    def __getitem__(self, item):
        """
        :param item:
        :return:
        """
        return self.data[item]

    def __setitem__(self, key, value):
        """
        :param key:
        :type key: int
        :param value:
        :type value: float
        :return:
        """
        self.data[key] = value

    def __getattr__(self, item):
        """

        :param item:
        :return:
        """
        try:
            idx = self.ATTRS.index(item)
        except:
            raise AttributeError("Unknown attribute `{}`".format(item))

        return self.data[idx]

    def __setattr__(self, key, value):
        """

        :param key:
        :param value:
        :return:
        """
        try:
            idx = self.ATTRS.index(key)
            self.data[idx] = value
            return value
        except ValueError:
            # Ignore error, just pass on to parent
            pass
        return super(VectorBase, self).__setattr__(key, value)

    def __iter__(self):
        """
        """
        return iter(self.data)

    def __len__(self):
        """
        :return: The length of this vector type
        :rtype: int
        """
        return len(self.data)

    def __abs__(self):
        """
        :return: Norm of this vector
        :rtype: float
        """
        return np.linalg.norm(self.data)

    def __neg__(self):
        """
        Return negative vector.
        :return:
        """
        return Vector3(-self.data)

    norm = __abs__
    magnitude = __abs__

    def normalize(self):
        """
        Normalizes this object
        """
        self.data /= self.norm()

    def normalized(self):
        """
        :return: Normalized version of this vector
        """
        return Vector3(self.data / self.norm())


class Vector3(VectorBase):
    """
    Defines an abstract vector data type as a wrapper
    over a numpy array.
    """
    LENGTH = 3
    ATTRS = 'xyz'

    def __init__(self, x=0, y=0, z=0):
        """
        :param x:
        :type x: float|iterable
        :param y:
        :type y: float
        :param z:
        :type z: float
        :return:
        """
        if hasattr(x, '__iter__'):
            super(Vector3, self).__init__(x)
        else:
            super(Vector3, self).__init__(x, y, z)

    def __repr__(self):
        """
        :return:
        """
        return 'Vector3(%e, %e, %e)' % tuple(self)

    def __add__(self, other):
        """

        :param other:
        :return:
        """
        if len(self) != len(other):
            raise AssertionError("Cannot add different length vectors.")
        return Vector3([x + y for x, y in zip(self, other)])

    def __sub__(self, other):
        """
        :param other:
        :return:
        """
        return Vector3([x - y for x, y in zip(self, other)])

    __radd__ = __add__
    __rsub__ = __sub__

    def __iadd__(self, other):
        """
        :param other:
        """
        if len(self) != len(other):
            raise AssertionError("Cannot add different length vectors.")
        self[0] += other[0]
        self[1] += other[1]
        self[2] += other[2]
        return self

    def __isub__(self, other):
        """
        :param other:
        """
        if len(self) != len(other):
            raise AssertionError("Cannot add different length vectors.")
        self[0] -= other[0]
        self[1] -= other[1]
        self[2] -= other[2]

    def __mul__(self, number):
        """
        :param number:
        :type number: float
        :return:
        """
        return Vector3(self[0] * number, self[1] * number, self[2] * number)

    def __imul__(self, number):
        """
        :param number:
        :type number: float
        :return:
        """
        self[0] *= number
        self[1] *= number
        self[2] *= number
        return self

    def __div__(self, number):
        """
        :param number:
        :type number: float
        :return:
        """
        return self.__mul__(1.0 / number)

    def __idiv__(self, number):
        """
        :param number:
        :type number: float
        :return:
        """
        return self.__imul__(1.0 / number)

    __rmul__ = __mul__
    __truediv__ = __div__

    def cross(self, v1):
        """
        Returns the cross product of this vector
        and the vector `v1`.
        :param v1:
        :type v1: Vector3
        :return:
        :rtype: Vector3
        """
        return Vector3(np.cross(self.data, v1.data))

    def dot(self, v1):
        """
        :param v1:
        :type v1: Vector3
        :return:
        """
        return np.dot(self.data, v1.data)

    def parallelism(self, other):
        """
        Check whether the given vectors parallel, opposite or not parallel.
        :param other:
        :type other: Vector3
        :return: Returns one of OPPOSITE / PARALLEL / NOT_PARALLEL "constants"
        :rtype: int
        """
        if not isinstance(other, Vector3):
            raise AssertionError("Vector is not an instance of Vector3")
        dot = self.normalized().dot(other.normalized())
        if dot <= (-1 + EPSILON):
            return OPPOSITE
        elif dot >= (1 - EPSILON):
            return PARALLEL
        else:
            return NOT_PARALLEL

    def parallel_to(self, b):
        """
        Shortcut method to `self.parallelism(a, b) == PARALLEL`
        :param b:
        :type b: Vector3
        :return:
        :rtype: bool
        """
        return self.parallelism(b) == PARALLEL

    def orthogonal_to(self, b):
        """
        Returns true if the two given vectors are orthogonal (i.e.
        their dot product is below a EPSILON)
        :param b:
        :type b: Vector3
        :return:
        :rtype bool
        """
        if not isinstance(b, Vector3):
            return AssertionError("Vector is not an instance of Vector3")
        return abs(self.normalized().dot(b.normalized())) <= EPSILON

    @staticmethod
    def from_vector3d(vector3d):
        return Vector3(vector3d.x, vector3d.y, vector3d.z)


class Quaternion(VectorBase):
    """
    Quaternion convenience class
    """
    LENGTH = 4
    ATTRS = 'wxyz'

    def __init__(self, w=1, x=0, y=0, z=0):
        """
        :param w:
        :param x:
        :param y:
        :param z:
        :return:
        """
        if hasattr(w, '__iter__'):
            super(Quaternion, self).__init__(w)
        else:
            super(Quaternion, self).__init__(w, x, y, z)

    def __repr__(self):
        """
        :return:
        """
        return 'Quaternion(real=%e, imag=<%e, %e, %e>)' % tuple(self)

    def __mul__(self, other):
        """

        :param other:
        :return:
        """
        if isinstance(other, Quaternion):
            return Quaternion(quaternion_multiply(self, other))
        elif isinstance(other, Vector3):
            # Get homogeneous rotation matrix and turn vector into
            # homogeneous vector.
            return self.get_matrix() * other

    def __imul__(self, other):
        """

        :param other:
        :return:
        """
        if not isinstance(other, Quaternion):
            raise AssertionError("Vector is not an instance of Quaternion")
        self.data[:] = quaternion_multiply(self, other)

    def get_matrix(self):
        """
        Returns the `RotationMatrix` for this quaternion
        :return:
        :rtype: RotationMatrix
        """
        return RotationMatrix(quaternion_matrix(self))

    def get_rpy(self):
        """
        Returns roll / pitch / yaw corresponding to this Quaternion
        """
        return euler_from_quaternion(self.data[:], 'sxyz')

    def conjugated(self):
        """
        :return:
        :rtype: Quaternion
        """
        return Quaternion(quaternion_conjugate(self))

    def inversed(self):
        """
        :return:
        :rtype: Quaternion
        """
        return Quaternion(quaternion_inverse(self))

    @staticmethod
    def from_angle_axis(angle, axis):
        """
        :param angle:
        :type angle: float
        :param axis:
        :type axis: Vector3
        :return:
        :rtype: Quaternion
        """
        return Quaternion(quaternion_about_axis(angle, axis))

    @staticmethod
    def from_rpy(roll, pitch, yaw):
        """
        Creates a quaternion from Gazebo roll, pitch, yaw values.
        :param roll:
        :type roll: float
        :param pitch:
        :type pitch: float
        :param yaw:
        :type yaw: float
        :return:
        """
        return Quaternion(quaternion_from_euler(roll, pitch, yaw, 'sxyz'))

    @staticmethod
    def from_quaternion(quaternion):
        return Quaternion(quaternion.w, quaternion.x, quaternion.y, quaternion.z)


class RotationMatrix(object):
    """
    Rotation matrix class
    """

    def __init__(self, data=None):
        """

        :param data:
        :return:
        """
        if data is None:
            self.data = np.identity(4)
        else:
            data = np.array(data, copy=True)
            if data.shape == (3, 3):
                self.data = np.identity(4)
                self.data[:3, :3] = data
            else:
                self.data = data

        if self.data.shape != (4, 4):
            raise AssertionError("Invalid data size.")

    def __copy__(self):
        """
        :return:
        """
        return self.__class__(self.data)

    copy = __copy__

    def __repr__(self):
        """
        :return:
        """
        return str(self.data[:3, :3])

    def __getitem__(self, item):
        """
        :param item:
        :return:
        """
        return self.data[item]

    def __setitem__(self, key, value):
        """
        :param key:
        :param value:
        :return:
        """
        self.data[key] = value

    def __iter__(self):
        """
        :return:
        """
        return iter(self.data)

    def __mul__(self, other):
        """
        :param other:
        :return:
        """
        if isinstance(other, RotationMatrix):
            return RotationMatrix(np.dot(self.data, other.data))
        elif isinstance(other, Vector3):
            vec = np.array([other.x, other.y, other.z, 1])
            return Vector3(np.dot(self.data, vec)[:3])
        else:
            raise ValueError(
                    "Unknown multiplication between `RotationMatrix` and "
                    "`{}`".format(other.__class__))

    def __imul__(self, other):
        """
        :param other:
        :return:
        """
        if not isinstance(other, RotationMatrix):
            raise AssertionError("Vector is not an instance of RotationMatrix")
        self.data = np.array(np.dot(self.data, other.data))

    def get_quaternion(self):
        """
        Returns the Quaternion for this rotation matrix
        :return:
        :rtype: Quaternion
        """
        return Quaternion(quaternion_from_matrix(self.data))

    def transpose(self):
        """
        Tranposes this RotationMatrix in place
        :return:
        """
        self.data = self.data.transpose()

    def transposed(self):
        """
        Returns a transposed version of this rotation matrix.
        :return:
        """
        return RotationMatrix(self.data.transpose())
