import numpy as np
import sys

from pyrevolve import URDF
from pyrevolve.URDF.inertial import transform_inertia_tensor
from pyrevolve.custom_logging.logger import logger


class Link(URDF.Posable):
    def __init__(self, name: str, self_collide=True, position=None, rotation=None):
        super().__init__(
            tag='link',
            attrib={'name': name},
            position=position,
            rotation=rotation,
        )
        # print(name)
        self.name = name
        self.size = (0, 0, 0, 0, 0, 0)
        self.inertial = None
        self.collisions = []
        self.joints = []
        self.CoM = URDF.math.Vector3(0, 0, 0)

    def iter_elements(self, condition):
        """
        Iterates all the elements that pass the condition statement
        :param condition: Condition to choose which element to iterate over
        :type condition: lambda function
        :return:
        """
        for elem in self.iter():
            if condition(elem):
                yield elem

    def append(self, subelement):
        """
        Appends an xml element to this object.

        If it's a collision, it saves it internally (for calculating the center of mass)
        :param subelement: XML Element to append
        """
        if type(subelement) is URDF.Collision:
            self.collisions.append(subelement)

        super().append(subelement)

    def align_center_of_mass(self):
        """
        Aligns the children posable objects relative to the center of mass of this link.

        It calculates the center of mass, and apply this as the center of the Link.
        All children posable are relative to the position of the Link, so their position needs
        to be adjusted.
        :return: the position of the center of mass
        :rtype: URDF.math.Vector3
        """
        translation = self.get_center_of_mass()
        # print(translation)
        # print(self.get_position())
        self.set_position(translation)
        # print(self.get_position())
        for el in self.iter_elements(lambda elem: isinstance(elem, URDF.Posable)):
            el.translate(-translation)
        for joint in self.joints:
            joint.translate(-translation)
        self.CoM = translation
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
            logger.warning("calculating inertial for link with nonzero center of mass.", file=sys.stderr)
        # print(self.get_center_of_mass(), f" INERTIA: {self.name}")
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

        self.inertial = URDF.Inertial.from_mass_matrix(total_mass, i_final)
        self.inertial.translate(self.CoM)
        for el in self.iter_elements(lambda elem: isinstance(elem, URDF.Posable)):
            el.translate(self.CoM)
        for joint in self.joints:
            joint.translate(self.CoM)
        self.append(self.inertial)

    def get_center_of_mass(self):
        """
        Calculate the center of mass of all the collisions inside
        this link.
        :return: The center of mass as determined by all the collision geometries
        :rtype: Vector3
        """
        com = URDF.math.Vector3(0, 0, 0)
        total_mass = 0.0
        for collision in self.collisions:
            col_com = collision.get_center_of_mass()
            mass = collision.mass
            com += mass * col_com
            total_mass += mass

        if total_mass > 0:
            com /= total_mass

        return com

    def add_joint(self, joint):
        """
        Add Joints to the internal list of joints.
        These joints position will be changed when the function `align_center_of_mass` is called.
        :param joint: joint whose children is this link
        :type joint: URDF.Joint
        """
        self.joints.append(joint)
