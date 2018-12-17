from __future__ import absolute_import

# Revolve imports
from ....build.sdf import BodyPart, ComponentJoint as Joint
from ....build.util import in_grams, in_mm

# SDF builder imports
from pyrevolve.sdfbuilder import Limit
from pyrevolve.sdfbuilder.math import Vector3
from pyrevolve.sdfbuilder.structure import Box

# Local imports
from .util import ColorMixin
from .. import constants

MASS_SLOT = in_grams(2)
MASS_FRAME = in_grams(3)

SLOT_WIDTH = in_mm(34)
SLOT_THICKNESS = in_mm(1.5)
CONNECTION_PART_LENGTH = in_mm(24)
CONNECTION_PART_HEIGHT = in_mm(10)

# Computed from the outermost corner of the connection part
CONNECTION_PART_OFFSET = in_mm(18.5)
SEPARATION = in_mm(0.1)


class Cardan(BodyPart, ColorMixin):
    """
    A passive cardan
    """

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        # Initialize the root, already at 0, 0, 0
        self.root = self.create_component(Box(SLOT_THICKNESS, SLOT_WIDTH, SLOT_WIDTH, MASS_SLOT), "root")

        # Initialize the first connection part
        x_part_a = 0.5 * (SLOT_THICKNESS + CONNECTION_PART_LENGTH) + SEPARATION
        conn_a = self.create_component(
            Box(CONNECTION_PART_LENGTH, SLOT_WIDTH, CONNECTION_PART_HEIGHT, MASS_FRAME), "conn_a")
        conn_a.set_position(Vector3(x_part_a, 0, 0))

        # Initialize the second connection part
        x_part_b = x_part_a - CONNECTION_PART_LENGTH + 2 * CONNECTION_PART_OFFSET
        conn_b = self.create_component(
            Box(CONNECTION_PART_LENGTH, CONNECTION_PART_HEIGHT, SLOT_WIDTH, MASS_FRAME), "conn_b")
        conn_b.set_position(Vector3(x_part_b, 0, 0))

        # Initialize the tail
        x_tail = x_part_b + 0.5 * (CONNECTION_PART_LENGTH + SLOT_THICKNESS) + SEPARATION
        self.tail = self.create_component(Box(SLOT_THICKNESS, SLOT_WIDTH, SLOT_WIDTH, MASS_SLOT), "tail")
        self.tail.set_position(Vector3(x_tail, 0, 0))

        # Fix the parts using joints
        # root <-> connection a
        self.fix(self.root, conn_a)

        # connection a <-> connection b
        cardan = Joint("universal", conn_a, conn_b, axis=Vector3(0, 0, 1), axis2=Vector3(0, 1, 0))
        limit = Limit(lower=-constants.CARDAN_LIMIT, upper=constants.CARDAN_LIMIT)
        cardan.axis.limit = cardan.axis2.limit = limit
        cardan.set_position(Vector3(0.5 * CONNECTION_PART_LENGTH - CONNECTION_PART_OFFSET))
        self.add_joint(cardan)

        # connection b <-> tail
        self.fix(conn_b, self.tail)

        # Apply color mixin
        self.apply_color()

    def get_slot(self, slot_id):
        self.check_slot(slot_id)
        return self.root if slot_id == 0 else self.tail

    def get_slot_position(self, slot_id):
        self.check_slot(slot_id)
        if slot_id == 0:
            return Vector3(-0.5 * SLOT_THICKNESS, 0, 0)
        else:
            return self.tail.to_sibling_frame(Vector3(0.5 * SLOT_THICKNESS, 0, 0), self)

    def get_slot_normal(self, slot_id):
        self.check_slot(slot_id)
        return Vector3(-1, 0, 0) if slot_id == 0 else Vector3(1, 0, 0)

    def get_slot_tangent(self, slot_id):
        self.check_slot(slot_id)
        return Vector3(0, 1, 0)
