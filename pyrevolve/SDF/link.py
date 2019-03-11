import xml.etree.ElementTree
import numpy as np

from pyrevolve import SDF
from pyrevolve.sdfbuilder import math as SDFmath
from pyrevolve.sdfbuilder.physics.inertial import transform_inertia_tensor


class Link(SDF.Posable):
    def __init__(self, name, self_collide=True, position=None, rotation=None):
        super().__init__(
            'link',
            {'name': name},
            position,
            rotation,
        )

        SDF.sub_element_text(self, 'self_collide', self_collide)
        self.size = (0, 0, 0, 0, 0, 0)
        self.inertial = None
        self.collisions = []

    def append(self, subelement):
        if type(subelement) is SDF.Collision:
            self.collisions.append(subelement)

        super().append(subelement)

    def align_center_of_mass(self):
        raise NotImplementedError("TODO")

    def calculate_inertial(self):
        """
        Calculates and sets this Link's inertial properties by
        iterating all collision elements inside of it and combining
        their Geometry's inertias.

        Note that in order for an inertia tensor to make sense in Gazebo,
        the center of mass needs to be aligned with the `Link` center of mass.
        This method prints an error if this is currently not the case.
        :return:
        """
        if not np.allclose(self.get_center_of_mass().norm(), 0):
            print("WARNING: calculating inertial for link with nonzero center of mass.", file=sys.stderr)

        i_final = np.zeros((3, 3))
        total_mass = 0.0
        for collision in self.collisions:
            rotation = collision.get_rotation()
            position = collision.get_position()
            geometry = collision.geometry
            mass = geometry.get_mass()
            total_mass += mass
            i_final += transform_inertia_tensor(
                mass,
                geometry.get_inertial().get_matrix(),
                position,
                rotation
            )

        self.inertial = Inertial.from_mass_matrix(total_mass, i_final)

    def get_center_of_mass(self):
        """
        Calculate the center of mass of all the collisions inside
        this link.
        :return: The center of mass as determined by all the collision geometries
        :rtype: Vector3
        """
        com = SDFmath.Vector3(0, 0, 0)
        total_mass = 0.0
        for collision in self.collisions:
            geometry = collision.geometry
            col_com = collision.to_parent_frame(geometry.get_center_of_mass())
            mass = geometry.get_mass()
            com += mass * col_com
            total_mass += mass

        if total_mass > 0:
            com /= total_mass

        return com


class Inertial(xml.etree.ElementTree.Element):
    def __init__(self, mass, inertia_xx, inertia_xy, inertia_xz, inertia_yy, inertia_yz, inertia_zz):
        super().__init__('inertial')

        SDF.sub_element_text(self, 'mass', mass)

        inertia = xml.etree.ElementTree.SubElement(self, 'inertia')
        SDF.sub_element_text(inertia, 'ixx', inertia_xx)
        SDF.sub_element_text(inertia, 'ixy', inertia_xy)
        SDF.sub_element_text(inertia, 'ixz', inertia_xz)
        SDF.sub_element_text(inertia, 'iyy', inertia_yy)
        SDF.sub_element_text(inertia, 'iyz', inertia_yz)
        SDF.sub_element_text(inertia, 'izz', inertia_zz)
