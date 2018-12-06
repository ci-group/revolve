from __future__ import absolute_import

# Revolve imports
from ....build.sdf import BodyPart, ComponentJoint as Joint
from ....build.util import in_grams, in_mm

from sdfbuilder.joint import Limit
from sdfbuilder.math import Vector3
from sdfbuilder.structure import Cylinder, Box

# Local imports
from .util import ColorMixin
from .. import constants

MASS_SLOT = in_grams(2.5)
MASS_WHEEL = in_grams(4)

SLOT_WIDTH = in_mm(34)
SLOT_THICKNESS = in_mm(10.75)
SLOT_CONNECTION_THICKNESS = in_mm(1.5)
SLOT_WHEEL_OFFSET = in_mm(7.5)
WHEEL_THICKNESS = in_mm(3)


class Wheel(BodyPart, ColorMixin):
    """
    Passive wheel
    """

    def _initialize(self, **kwargs):
        self.radius = in_mm(kwargs['radius'])

        wheel = self.create_component(Cylinder(self.radius, WHEEL_THICKNESS, MASS_WHEEL), "wheel")
        self.root = self.create_component(Box(SLOT_WIDTH, SLOT_WIDTH, SLOT_THICKNESS, MASS_SLOT))

        # Create the wheel
        z_wheel = 0.5 * SLOT_THICKNESS - (SLOT_THICKNESS + SLOT_CONNECTION_THICKNESS - SLOT_WHEEL_OFFSET)
        wheel.set_position(Vector3(0, 0, z_wheel))

        # Attach the wheel and the root with a revolute joint
        joint = Joint("revolute", self.root, wheel, axis=Vector3(0, 0, -1))

        # TODO Adequate force limit for passive wheel
        joint.axis.limit = Limit(effort=constants.MAX_SERVO_TORQUE_ROTATIONAL)
        self.add_joint(joint)

        # Call color mixin
        self.apply_color()

    def get_slot(self, slot_id):
        self.check_slot(slot_id)
        return self.root

    def get_slot_position(self, slot_id):
        return Vector3(0, 0, -0.5 * SLOT_THICKNESS)

    def get_slot_normal(self, slot_id):
        return Vector3(0, 0, -1)

    def get_slot_tangent(self, slot_id):
        return Vector3(0, 1, 0)
