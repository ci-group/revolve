from __future__ import absolute_import
from __future__ import division

# Revolve / sdfbuilder imports
from ....build.sdf import Box
from ....build.util import in_grams, in_mm
from pyrevolve.sdfbuilder.structure import Box as BoxGeom, Mesh
from pyrevolve.sdfbuilder.math import Vector3

# Local imports
from .util import ColorMixin

WIDTH = in_mm(41)
HEIGHT = in_mm(35.5)
MASS = in_grams(10.2)


class FixedBrick(Box, ColorMixin):
    """
    Brick - same size as the core component, but
    without any sensors. We can conveniently model this
    as a box.
    """
    X = WIDTH
    Y = WIDTH
    Z = HEIGHT
    MASS = MASS

    def _initialize(self, **kwargs):
        self.component = self.create_component(
            BoxGeom(self.x, self.y, self.z, self.mass), "box",
            visual=Mesh("model://rg_robot/meshes/FixedBrick.dae"))
        self.apply_color()

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
        vmax = WIDTH / 2.0
        if slot == 0:
            # Front face
            return Vector3(0, -vmax, 0)
        elif slot == 1:
            # Back face
            return Vector3(0, vmax, 0)
        elif slot == 2:
            # Right face
            return Vector3(vmax, 0, 0)

        # Left face
        return Vector3(-vmax, 0, 0)

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

        # The top face is tangent to all supported
        # slots in the plane, front, back, right, left
        # Since there's no particular reason for choosing any
        # other we just return the top face for all.
        return Vector3(0, 0, 1)
