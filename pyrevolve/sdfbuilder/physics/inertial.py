from ..element import Element
from ..util import number_format as nf
import numpy as np


def transform_inertia_tensor(mass, tensor, displacement, rotation):
    """
    Transforms an inertia tensor to a new reference frame using
    the parallel axis theorem.

    https://en.wikipedia.org/wiki/Parallel_axis_theorem
    :param mass:
    :type mass: float
    :param tensor: The inertia tensor as a numpy array
    :type tensor: ndarray
    :param displacement: The displacement vector `d`, where `d` is
                         the new center of mass minus the current
                         center of mass (i.e. traveling `d` from the
                         current center of mass gives the new center
                         of mass).
    :type displacement: Vector3
    :param rotation: The rotation that takes a point in the current tensor
                     reference frame to one in the new reference frame.
    :type rotation: Quaternion
    :return:
    """
    # Short hand
    i1 = tensor
    t1 = displacement

    # Get a matrix for the rotation and calculate the
    # rotated inertia tensor.
    r1 = rotation.get_matrix()[:3, :3]
    it = r1.dot(i1).dot(r1.T)

    # J matrix as on Wikipedia
    return it + mass * (t1.dot(t1) * np.eye(3) - np.outer(t1.data, t1.data))


class Inertial(Element):
    """
    Convenience class for inertial elements
    """
    TAG_NAME = 'inertial'

    def __init__(self, mass=1.0, ixx=0, iyy=0, izz=0, ixy=0, ixz=0, iyz=0, **kwargs):
        """
        :param mass:
        :param ixx:
        :param iyy:
        :param izz:
        :param ixy:
        :param ixz:
        :param iyz:
        :param kwargs:
        """
        super(Inertial, self).__init__(**kwargs)

        self.ixx, self.ixy, self.ixz = (ixx, ixy, ixz)
        self.iyy, self.iyz = (iyy, iyz)
        self.izz = izz
        self.mass = mass

    def render_body(self):
        """
        Adds inertia to body before render.
        :return:
        """
        body = super(Inertial, self).render_body()
        body += "<mass>%s</mass>" % nf(self.mass)
        body += ("<inertia>"
                 "<ixx>%s</ixx>"
                 "<ixy>%s</ixy>"
                 "<ixz>%s</ixz>"
                 "<iyy>%s</iyy>"
                 "<iyz>%s</iyz>"
                 "<izz>%s</izz>"
                 "</inertia>" % (nf(self.ixx), nf(self.ixy), nf(self.ixz),
                                 nf(self.iyy), nf(self.iyz), nf(self.izz)))
        return body

    @staticmethod
    def from_mass_matrix(mass, m):
        """
        :param mass:
        :param m:
        :return:
        """
        return Inertial(mass, ixx=m[0, 0], ixy=m[0, 1],
                        ixz=m[0, 2], iyy=m[1, 1], iyz=m[1, 2],
                        izz=m[2, 2])

    def transformed(self, displacement, rotation):
        """
        Returns a new inertial from this one, which is
        transformed to a new reference frame given by a
        displacement and rotation vector.
        :param displacement:
        :param rotation:
        :return:
        """
        transformed = transform_inertia_tensor(self.mass, self.get_matrix(),
                                               displacement, rotation)
        return self.from_mass_matrix(self.mass, transformed)

    def get_matrix(self):
        """
        :return:
        """
        return np.array([
            [self.ixx, self.ixy, self.ixz],
            [self.ixy, self.iyy, self.iyz],
            [self.ixz, self.iyz, self.izz]
        ])
