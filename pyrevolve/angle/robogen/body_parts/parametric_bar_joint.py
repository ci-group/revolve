from __future__ import absolute_import
from __future__ import print_function

# Revolve imports
from ....build.sdf import BodyPart
from ....build.util import in_grams, in_mm

# sdfbuilder imports
from pyrevolve.sdfbuilder.math import Vector3
from pyrevolve.sdfbuilder.structure import Box

# Local imports
from .util import ColorMixin


class ParametricBarJoint(BodyPart, ColorMixin):
    """
    The parametric bar joint allows the introduction of fix
    angles into your robot and can also be useful
    depending on the needs to space components of your robot.
    Three parameters can be controlled:

    - The length of the joint (H, between 2 and 10 centimeters),
    - its tilt (alpha, between -pi/2 and pi/2) and
    - its rotation (beta, between 0 and pi).

    Compared to the fixed brick or core component, the parametric bar joint
    is somewhat frail and should not be exposed to too much mechanical stress.
    """
    MASS_SLOT = in_grams(1)
    MASS_CONNECTION_PER_CM = in_grams(2)
    SLOT_WIDTH = in_mm(34)
    SLOT_THICKNESS = in_mm(1.5)
    CONNECTION_PART_WIDTH = in_mm(20)
    CONNECTION_PART_THICKNESS = in_mm(2)
    SEPARATION = in_mm(0)

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        # Variable shorthands
        mass = self.MASS_SLOT
        thickness = self.SLOT_THICKNESS
        width = self.SLOT_WIDTH
        conn_width = self.CONNECTION_PART_WIDTH
        conn_thickness = self.CONNECTION_PART_THICKNESS
        mass_per_cm = self.MASS_CONNECTION_PER_CM
        sep = self.SEPARATION

        # Connection length is in mm
        self.conn_length = conn_length = in_mm(kwargs['connection_length'])

        # Initialize root
        self.root = self.create_component(Box(thickness, width, width, mass), "root")

        # Initialize connection
        x_connection = 0.5 * (thickness + conn_length) + sep
        connection = self.create_component(
            Box(conn_length, conn_width, conn_thickness, 10 * mass_per_cm * conn_length), "connection")
        connection.set_position(Vector3(x_connection, 0, 0))

        # Tail
        x_slot_b = x_connection + 0.5 * (conn_length + thickness) + sep
        self.tail = self.create_component(Box(thickness, width, width, mass), "tail")
        self.tail.set_position(Vector3(x_slot_b, 0, 0))

        # Create fixed joints between the parts
        # root <> connection
        self.fix(self.root, connection)

        # connection <> tail
        self.fix(connection, self.tail)

        # Now perform the rotations. `BodyPart` guarantees
        # that it has origin position and zero orientation
        # at initialisation time, as to avoid confusion with
        # `relative_to_child`.
        self.tilt = tilt = kwargs['alpha']
        self.rotation = rotation = kwargs['beta']

        # First rotate the connection and the tail over beta
        rotation_axis = Vector3(1, 0, 0)
        connection.rotate_around(rotation_axis, rotation,
                                 relative_to_child=False)
        self.tail.rotate_around(rotation_axis, rotation,
                                relative_to_child=False)

        # First tilt the tail over alpha
        self.tail.rotate_around(Vector3(0, 1, 0), tilt,
                                relative_to_child=True)

        # Trigger color mixin
        self.apply_color()

    def get_slot(self, slot_id):
        self.check_slot(slot_id)
        return self.root if slot_id == 0 else self.tail

    def get_slot_position(self, slot_id):
        self.check_slot(slot_id)
        offset = 0.5 * self.SLOT_THICKNESS

        if slot_id == 0:
            # Root has no relative pose so this is easy
            return Vector3(-offset, 0, 0)
        else:
            # This is a posable group, so we must use
            # sibling conversion.
            return self.tail.to_sibling_frame(
                Vector3(offset, 0, 0),
                self
            )

    def get_slot_tangent(self, slot_id):
        self.check_slot(slot_id)
        vec = Vector3(0, 1, 0)
        return vec if slot_id == 0 else self.tail.to_sibling_direction(
            vec, self
        )

    def get_slot_normal(self, slot_id):
        self.check_slot(slot_id)

        if slot_id == 0:
            return Vector3(-1, 0, 0)
        else:
            return self.tail.to_sibling_direction(
                Vector3(1, 0, 0),
                self
            )
