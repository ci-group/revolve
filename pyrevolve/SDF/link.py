import numpy as np
import sys

from pyrevolve import SDF
from pyrevolve.SDF.inertial import transform_inertia_tensor
from pyrevolve.sdfbuilder import math as SDFmath


class Link(SDF.Posable):
    def __init__(self, name, self_collide=True, position=None, rotation=None):
        super().__init__(
            tag='link',
            attrib={'name': name},
            position=position,
            rotation=rotation,
        )

        SDF.sub_element_text(self, 'self_collide', self_collide)
        self.size = (0, 0, 0, 0, 0, 0)
        self.inertial = None
        self.collisions = []

    def iter_elements(self, condition):
        for elem in self.iter():
            if condition(elem):
                yield elem

    def append(self, subelement):
        if type(subelement) is SDF.Collision:
            self.collisions.append(subelement)

        super().append(subelement)

    def align_center_of_mass(self):
        translation = self.get_center_of_mass()
        self.set_position(translation*2.0)
        for el in self.iter_elements(lambda elem: isinstance(elem, SDF.Posable)):
            el.translate(-translation)
        return translation

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
        if self.inertial is not None:
            raise RuntimeError("Inertial for this link already existing")

        if not np.allclose(self.get_center_of_mass().norm(), 0):
            print("WARNING: calculating inertial for link with nonzero center of mass.", file=sys.stderr)

        i_final = np.zeros((3, 3))
        total_mass = 0.0
        for collision in self.collisions:
            rotation = collision.get_rotation()
            position = collision.get_position()
            mass = collision.mass
            total_mass += mass
            i_final += transform_inertia_tensor(
                mass,
                collision.get_inertial().get_matrix(),
                position,
                rotation
            )

        self.inertial = SDF.Inertial.from_mass_matrix(total_mass, i_final)
        self.append(self.inertial)

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
            col_com = collision.get_center_of_mass()
            mass = collision.mass
            com += mass * col_com
            total_mass += mass

        if total_mass > 0:
            com /= total_mass

        return com


