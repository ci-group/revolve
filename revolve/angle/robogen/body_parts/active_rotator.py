from __future__ import absolute_import

# Revolve imports
from ....build.sdf import BodyPart, PositionMotor, ComponentJoint as Joint
from ....build.util import in_grams, in_mm

from revolve.sdfbuilder.joint import Limit
from revolve.sdfbuilder.math import Vector3
from revolve.sdfbuilder.structure import Box

# Local imports
from .util import ColorMixin
from .. import constants

MASS_SLOT = in_grams(4)
MASS_SERVO = in_grams(9)
MASS_CONNECTION_SLOT = in_grams(2)

SLOT_WIDTH = in_mm(34)
SLOT_THICKNESS = in_mm(1.5)
SERVO_Z_OFFSET = in_mm(0)
SERVO_WIDTH = in_mm(14)
SERVO_LENGTH = in_mm(36.8)
SERVO_HEIGHT = in_mm(14)
JOINT_CONNECTION_THICKNESS = in_mm(7.5)
JOINT_CONNECTION_WIDTH = in_mm(34)
SEPARATION = in_mm(0.1)


class ActiveRotator(BodyPart, ColorMixin):
    """
    Active wheel
    """

    def _initialize(self, **kwargs):
        # Initialize the root
        self.root = self.create_component(Box(SLOT_THICKNESS, SLOT_WIDTH, SLOT_WIDTH, MASS_SLOT), "root")

        # Initialize the servo
        servo = self.create_component(Box(SERVO_LENGTH, SERVO_WIDTH, SERVO_HEIGHT, MASS_SERVO))
        x_servo = 0.5 * (SLOT_THICKNESS + SERVO_LENGTH) + SEPARATION
        # z_servo = 0.5 * (SERVO_HEIGHT - SLOT_WIDTH) + SERVO_Z_OFFSET
        z_servo = 0
        servo.set_position(Vector3(x_servo, 0, z_servo))

        # Initialize the connection
        self.connection = self.create_component(Box(JOINT_CONNECTION_THICKNESS, JOINT_CONNECTION_WIDTH,
                                                    JOINT_CONNECTION_WIDTH, MASS_CONNECTION_SLOT), "connection")
        x_conn = x_servo + 0.5 * (SERVO_LENGTH - JOINT_CONNECTION_THICKNESS) + SEPARATION
        self.connection.set_position(Vector3(x_conn, 0, 0))

        # Fix the links
        # root <-> servo
        self.fix(self.root, servo)

        # servo <revolute> connection
        self.joint = Joint("revolute", servo, self.connection, axis=Vector3(1, 0, 0))
        self.joint.axis.limit = Limit(
            effort=constants.MAX_SERVO_TORQUE_ROTATIONAL,
            velocity=constants.MAX_SERVO_VELOCITY
        )
        self.add_joint(self.joint)

        # Now we add a motor that powers the joint. This particular servo
        # targets a velocity. Use a simple PID controller initially.
        pid = constants.SERVO_POSITION_PID
        self.motors.append(PositionMotor(self.id, "rotate", self.joint, pid))

        # Call color mixin
        self.apply_color()

    def get_slot(self, slot_id):
        self.check_slot(slot_id)
        return self.root if slot_id == 0 else self.connection

    def get_slot_position(self, slot_id):
        self.check_slot(slot_id)
        if slot_id == 0:
            return Vector3(-0.5 * SLOT_THICKNESS, 0, 0)
        else:
            return self.connection.to_sibling_frame(
                Vector3(0.5 * JOINT_CONNECTION_THICKNESS, 0, 0), self)

    def get_slot_normal(self, slot_id):
        self.check_slot(slot_id)
        return Vector3(-1, 0, 0) if slot_id == 0 else Vector3(1, 0, 0)

    def get_slot_tangent(self, slot_id):
        return Vector3(0, 1, 0)
