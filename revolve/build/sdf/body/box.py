from sdfbuilder.structure import Box as BoxGeom
from sdfbuilder.math import Vector3
from .body_part import BodyPart


class Box(BodyPart):
    """
    A base class that allows to you quickly define a body part
    that is just a simple box.
    """
    # Override these in child class for direct simple box
    MASS = 1.0
    X = 1.0
    Y = 1.0
    Z = 1.0

    def __init__(self, id, conf, **kwargs):
        """

        :param args:
        :param kwargs:
        :return:
        """
        # Set class properties here, if desired they can
        # still be overwritten in _initialize.
        self.x, self.y, self.z = self.X, self.Y, self.Z
        self.mass = self.MASS

        super(Box, self).__init__(id, conf, **kwargs)

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        self.component = self.create_component(BoxGeom(self.x, self.y, self.z, self.mass), "box")

    def get_slot(self, slot):
        """
        There's only one slot, return the link.
        """
        self.check_slot(slot)
        return self.component

    def get_slot_position(self, slot):
        """
        Return slot position
        """
        self.check_slot(slot)
        xmax, ymax, zmax = self.x / 2.0, self.y / 2.0, self.z / 2.0
        if slot == 0:
            # Front face
            return Vector3(0, -ymax, 0)
        elif slot == 1:
            # Back face
            return Vector3(0, ymax, 0)
        elif slot == 2:
            # Top face
            return Vector3(0, 0, zmax)
        elif slot == 3:
            # Bottom face
            return Vector3(0, 0, -zmax)
        elif slot == 4:
            # Right face
            return Vector3(xmax, 0, 0)

        # Left face
        return Vector3(-xmax, 0, 0)

    def get_slot_normal(self, slot):
        """
        Return slot normal.
        """
        return self.get_slot_position(slot).normalized()

    def get_slot_tangent(self, slot):
        """
        Return slot tangent
        """
        self.check_slot(slot)
        if slot == 0:
            # Front face tangent: top face
            return Vector3(0, 0, 1)
        elif slot == 1:
            # Back face tangent: top face
            return Vector3(0, 0, 1)
        elif slot == 2:
            # Top face tangent: right face
            return Vector3(1, 0, 0)
        elif slot == 3:
            # Bottom face tangent: right face
            return Vector3(1, 0, 0)
        elif slot == 4:
            # Right face tangent: back face
            return Vector3(0, 1, 0)

        # Left face tangent: back face
        return Vector3(0, 1, 0)
