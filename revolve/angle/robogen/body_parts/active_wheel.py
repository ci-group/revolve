from __future__ import absolute_import

# Revolve imports
from ....build.sdf import BodyPart, VelocityMotor, ComponentJoint as Joint
from ....build.util import in_grams, in_mm

from sdfbuilder.joint import Limit
from sdfbuilder.math import Vector3
from sdfbuilder.structure import Cylinder, Box

# Local imports
from .util import ColorMixin
from .. import constants

MASS_SLOT = in_grams(4)
MASS_SERVO = in_grams(9)
MASS_WHEEL = in_grams(5)
SLOT_WIDTH = in_mm(34)
SLOT_THICKNESS = in_mm(1.5)
SERVO_WIDTH = in_mm(14)
WHEEL_THICKNESS = in_mm(3)
SERVO_LENGTH = in_mm(36.8) - WHEEL_THICKNESS
SERVO_HEIGHT = in_mm(14)
SEPARATION = in_mm(1.0)
X_SERVO = -SLOT_THICKNESS + SEPARATION + 0.5 * SERVO_LENGTH
X_WHEEL = X_SERVO + 0.5 * SERVO_LENGTH

class ActiveWheel(BodyPart, ColorMixin):
    """
    Active wheel
    """

    def _initialize(self, **kwargs):
        self.radius = in_mm(kwargs['radius'])

        # Create the root
        self.root = self.create_component(
            Box(SLOT_WIDTH, SLOT_WIDTH, SLOT_THICKNESS, MASS_SLOT), "root")

        # Create the servo
        servo = self.create_component(Box(SERVO_HEIGHT, SERVO_WIDTH, SERVO_LENGTH, MASS_SERVO), "servo")
        servo.set_position(Vector3(0, 0, X_SERVO))

        # Create the wheel
        wheel = self.create_component(Cylinder(self.radius, WHEEL_THICKNESS, MASS_WHEEL), "wheel")
        wheel.set_position(Vector3(0, 0, X_WHEEL))

        # Fix the root to the servo
        self.fix(self.root, servo)

        # Attach the wheel and the root with a revolute joint
        self.joint = Joint("revolute", servo, wheel, axis=Vector3(0, 0, -1))
        self.joint.set_position(Vector3(0, 0, -WHEEL_THICKNESS))
        self.joint.axis.limit = Limit(
            effort=constants.MAX_SERVO_TORQUE_ROTATIONAL,
            velocity=constants.MAX_SERVO_VELOCITY
        )
        self.add_joint(self.joint)

        # Now we add a motor that powers the joint. This particular servo
        # targets a velocity. Use a simple PID controller initially.
        pid = constants.SERVO_VELOCITY_PID
        self.motors.append(VelocityMotor(
            self.id, "rotate", self.joint, pid=pid,
            max_velocity=constants.MAX_SERVO_VELOCITY,
            min_velocity=-constants.MAX_SERVO_VELOCITY
        ))

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
