import xml.etree
import numpy as np

from pyrevolve import SDF


class Inertial(SDF.Posable):
    def __init__(self, mass, position=None, rotation=None,
                 inertia_xx=1.0, inertia_xy=0.0, inertia_xz=0.0,
                 inertia_yy=1.0, inertia_yz=0.0,
                 inertia_zz=1.0):
        super().__init__('inertial', position=position, rotation=rotation)
        self.ixx, self.ixy, self.ixz = (inertia_xx, inertia_xy, inertia_xz)
        self.iyy, self.iyz = (inertia_yy, inertia_yz)
        self.izz = inertia_zz
        self.mass = mass

        SDF.sub_element_text(self, 'mass', mass)

        inertia = xml.etree.ElementTree.SubElement(self, 'inertia')
        SDF.sub_element_text(inertia, 'ixx', inertia_xx)
        SDF.sub_element_text(inertia, 'ixy', inertia_xy)
        SDF.sub_element_text(inertia, 'ixz', inertia_xz)
        SDF.sub_element_text(inertia, 'iyy', inertia_yy)
        SDF.sub_element_text(inertia, 'iyz', inertia_yz)
        SDF.sub_element_text(inertia, 'izz', inertia_zz)

    @staticmethod
    def from_mass_matrix(mass, m):
        """
        :param mass:
        :param m:
        :return:
        """
        return Inertial(mass, position=None, rotation=None,
                        inertia_xx=m[0, 0], inertia_xy=m[0, 1], inertia_xz=m[0, 2],
                        inertia_yy=m[1, 1], inertia_yz=m[1, 2],
                        inertia_zz=m[2, 2])

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
