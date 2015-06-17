from sdfbuilder.math import Vector3
from sdfbuilder.structure import Cylinder as CylinderGeom
from .body_part import BodyPart


class Cylinder(BodyPart):
    """
    A base class that allows you to quicky define a body
    part that is just a simple cylinder.

    By default a cylinder has two slots: one on the center of each
    flat side.
    """
    # Override these in child class for basic functionality
    MASS = 1.0
    """The mass of the box"""

    RADIUS = 1.0
    """ The radius of the cylinder (in x and y directions)"""

    LENGTH = 1.0
    """ The length of the cylinder (in z direction) """

    def __init__(self, part_id, conf, **kwargs):
        """
        """
        # Set class properties here, if desired they can
        # still be overwritten in _initialize.
        self.mass, self.radius, self.length = self.MASS, self.RADIUS, self.LENGTH
        super(Cylinder, self).__init__(part_id, conf, **kwargs)

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        self.component = self.create_component(CylinderGeom(
            self.radius, self.length, self.mass), "cylinder")

    def get_slot(self, slot_id):
        """
        :param slot_id:
        :return:
        """
        self.check_slot(slot_id)
        return self.component

    def get_slot_position(self, slot_id):
        """
        Returns the slot position for the given slot. Slot 0 is
        defined as the top, slot 1 is the bottom.
        :param slot_id:
        :return:
        """
        z = self.length / 2.0
        return Vector3(0, 0, z if slot_id == 0 else -z)

    def get_slot_normal(self, slot_id):
        """
        :param slot_id:
        :return:
        """
        return self.get_slot_position(slot_id).normalized()

    def get_slot_tangent(self, slot_id):
        """
        We use the same tangent vector for every slot, pointing
        horizontally.
        :param slot_id:
        :return:
        """
        return Vector3(1, 0, 0)

