from __future__ import absolute_import
from __future__ import division

# SDF builder imports
from pyrevolve.sdfbuilder.math import Vector3
from pyrevolve.sdfbuilder.joint import Limit
from pyrevolve.sdfbuilder.structure import Box, Mesh, Visual

# Revolve imports
from ....build.sdf import BodyPart, PositionMotor, ComponentJoint as Joint
from ....build.util import in_grams, in_mm

# Local imports
from .util import ColorMixin
from .. import constants

MASS_SLOT = in_grams(7)
MASS_SERVO = in_grams(9)
MASS_FRAME = in_grams(1.2)
SLOT_WIDTH = in_mm(34)
SLOT_THICKNESS = in_mm(1.5)

FRAME_LENGTH = in_mm(18)
FRAME_HEIGHT = in_mm(10)
FRAME_ROTATION_OFFSET = in_mm(14)
""" Left to right """

SERVO_LENGTH = in_mm(24.5)
SERVO_HEIGHT = in_mm(10)
SERVO_ROTATION_OFFSET = in_mm(20.5)
""" Right to left """

SEPARATION = in_mm(0.1)


class ActiveHinge(BodyPart, ColorMixin):
    """
    A passive hinge
    """

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        # Shorthand for variables
        # Initialize root
        self.hinge_root = self.create_component(
            Box(SLOT_THICKNESS, SLOT_WIDTH, SLOT_WIDTH, MASS_SLOT), "root")

        # Make frame
        visual1 = Visual("frame_visual", Mesh("model://rg_robot/meshes/ActiveHinge_Frame.dae"))
        frame = self.create_component(Box(FRAME_LENGTH, SLOT_WIDTH, FRAME_HEIGHT, MASS_FRAME),
                                      "frame", visual=visual1)
        x_frame = SLOT_THICKNESS / 2.0 + SEPARATION + FRAME_LENGTH / 2.0
        frame.set_position(Vector3(x_frame, 0, 0))

        # Make servo
        visual2 = Visual("servo_visual", Mesh("model://rg_robot/meshes/ActiveCardanHinge_Servo_Holder.dae"))
        servo = self.create_component(Box(SERVO_LENGTH, SLOT_WIDTH, SERVO_HEIGHT, MASS_SERVO),
                                      "servo", visual=visual2)
        x_servo = x_frame + (FRAME_ROTATION_OFFSET - 0.5 * FRAME_LENGTH) + \
                  (-0.5 * SERVO_LENGTH + SERVO_ROTATION_OFFSET)
        servo.set_position(Vector3(x_servo, 0, 0))

        # TODO Color servo?

        # Make the tail. Visual is provided by Servo_Holder above.
        self.hinge_tail = self.create_component(Box(SLOT_THICKNESS, SLOT_WIDTH, SLOT_WIDTH, MASS_SLOT),
                                                "tail", visual=False)
        x_tail = x_servo + SERVO_LENGTH / 2.0 + SEPARATION + SLOT_THICKNESS / 2.0
        self.hinge_tail.set_position(Vector3(x_tail, 0, 0))

        # Create joints to hold the pieces in position
        # root <-> frame
        self.fix(self.hinge_root, frame)

        # Connection part a <(hinge)> connection part b
        # Hinge joint axis should point straight up, and anchor
        # the points in the center. Note that the position of a joint
        # is expressed in the child link frame, so we need to take the
        # position from the original code and subtract conn_b's position
        self.joint = Joint("revolute", servo, frame, axis=Vector3(0, 1, 0))
        self.joint.set_position(Vector3(-0.5 * FRAME_LENGTH + FRAME_ROTATION_OFFSET, 0, 0))
        self.joint.axis.limit = Limit(
            lower=-constants.SERVO_LIMIT,
            upper=constants.SERVO_LIMIT,
            effort=constants.MAX_SERVO_TORQUE,
            velocity=constants.MAX_SERVO_VELOCITY
        )
        self.add_joint(self.joint)

        # connection part b <-> tail
        self.fix(servo, self.hinge_tail)

        # Now we add a motor that powers the joint. This particular servo
        # targets a position. Use a simple PID controller initially.
        pid = constants.SERVO_POSITION_PID
        self.motors.append(PositionMotor(
                part_id=self.id,
                motor_id="rotate",
                joint=self.joint,
                pid=pid,
                x=self.x,
                y=self.y
        ))

        # Apply color mixin
        self.apply_color()

    def get_slot_normal(self, slot_id):
        return self.get_slot_position(slot_id).normalized()

    def get_slot_tangent(self, slot_id):
        self.check_slot(slot_id)
        return Vector3(0, 0, 1)

    def get_slot(self, slot_id):
        self.check_slot(slot_id)
        return self.hinge_root if slot_id == 0 else self.hinge_tail

    def get_slot_position(self, slot_id):
        self.check_slot(slot_id)

        offset = 0.5 * SLOT_THICKNESS
        if slot_id == 0:
            # The root slot is positioned half the slot
            # thickness to the left
            return Vector3(-offset, 0, 0)
        else:
            # A `BodyPart` is a posable group, so item positions are
            # in the parent frame. If we convert to the local frame we can
            # simply add the offset in the x-direction
            tail_pos = self.to_local_frame(self.hinge_tail.get_position())
            return tail_pos + Vector3(offset, 0, 0)
