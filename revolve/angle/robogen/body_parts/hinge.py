# Revolve imports
from __future__ import absolute_import
import math
from ....build.sdf import BodyPart, ComponentJoint as Joint
from ....build.util import in_grams, in_mm

# SDF builder imports
from sdfbuilder import Limit
from sdfbuilder.math import Vector3
from sdfbuilder.structure import Box, Mesh, Visual

# Local imports
from .util import ColorMixin
from .. import constants

MASS_SLOT = in_grams(2)
MASS_FRAME = in_grams(1)
SLOT_WIDTH = in_mm(34)
SLOT_THICKNESS = in_mm(1.5)
CONNECTION_PART_LENGTH = in_mm(20.5)
CONNECTION_PART_HEIGHT = in_mm(20)
CONNECTION_PART_THICKNESS = in_mm(2)
CONNECTION_ROTATION_OFFSET = in_mm(18.5)
""" Computed from the left corner of the connection part. """

SEPARATION = in_mm(0.1)


class Hinge(BodyPart, ColorMixin):
    """
    A passive hinge
    """

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        # Create components. Visuals are provided by the conn_a/conn_b meshes
        self.hinge_root = self.create_component(
            Box(SLOT_THICKNESS, SLOT_WIDTH, SLOT_WIDTH, MASS_SLOT), "slot_a",
            visual=False)
        self.hinge_tail = self.create_component(
            Box(SLOT_THICKNESS, SLOT_WIDTH, SLOT_WIDTH, MASS_SLOT), "slot_b",
            visual=False)
        mesh = Mesh("model://rg_robot/meshes/PassiveHinge.dae")
        visual_a = Visual("conn_a_visual", mesh)
        visual_a.translate(Vector3(-0.5 * SLOT_THICKNESS))
        conn_a = self.create_component(
            Box(CONNECTION_PART_LENGTH, CONNECTION_PART_THICKNESS, CONNECTION_PART_HEIGHT, MASS_FRAME),
            "conn_a", visual=visual_a)

        # Flip visual along the x-axis by rotating PI degrees over z
        # This will put it upside down, so we also flip it PI degrees over x
        visual_b = Visual("conn_b_visual", mesh.copy())
        visual_b.rotate_around(Vector3(1, 0, 0), math.pi, relative_to_child=False)
        visual_b.rotate_around(Vector3(0, 0, 1), math.pi, relative_to_child=False)
        visual_b.translate(Vector3(0.5 * SLOT_THICKNESS))
        conn_b = self.create_component(
            Box(CONNECTION_PART_LENGTH, CONNECTION_PART_THICKNESS, CONNECTION_PART_HEIGHT, MASS_FRAME),
            "conn_b", visual=visual_b)

        # Shorthand for variables
        # Position connection part a
        x_part_a = SLOT_THICKNESS / 2.0 + SEPARATION + CONNECTION_PART_LENGTH / 2.0
        conn_a.set_position(Vector3(x_part_a, 0, 0))

        # Position connection part b
        x_part_b = x_part_a + (CONNECTION_PART_LENGTH / 2.0 - (CONNECTION_PART_LENGTH - CONNECTION_ROTATION_OFFSET)) * 2
        conn_b.set_position(Vector3(x_part_b, 0, 0))

        # Make the tail
        x_tail = x_part_b + CONNECTION_PART_LENGTH / 2.0 + SEPARATION + SLOT_THICKNESS / 2.0
        self.hinge_tail.set_position(Vector3(x_tail, 0, 0))

        # Fix components
        self.fix(self.hinge_root, conn_a)
        self.fix(self.hinge_tail, conn_b)

        # Connection part a <(hinge)> connection part b
        # Hinge joint axis should point straight up, and anchor
        # the points in the center. Note that the position of a joint
        # is expressed in the child link frame, so we need to take the
        # position from the original code and subtract conn_b's position
        self.joint = Joint("revolute", conn_a, conn_b, axis=Vector3(0, 0, 1))
        self.joint.set_position(Vector3(CONNECTION_PART_LENGTH / 2.0 - CONNECTION_ROTATION_OFFSET, 0, 0))
        self.joint.axis.limit = Limit(
            upper=constants.HINGE_LIMIT,
            lower=-constants.HINGE_LIMIT
        )
        self.add_joint(self.joint)

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
            return self.hinge_root.to_sibling_frame(
                Vector3(-offset, 0, 0),
                self
            )
        else:
            # A `BodyPart` is a PosableGroup, so child positions are
            # similar to sibling positions. We can thus take the position
            # in the tail, and use sibling conversion to get the position
            # in the body part.
            return self.hinge_tail.to_sibling_frame(
                Vector3(offset, 0, 0),
                self
            )
