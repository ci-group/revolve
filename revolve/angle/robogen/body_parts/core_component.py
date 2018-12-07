# System imports
from __future__ import absolute_import
from __future__ import division

# SDF builder imports
from revolve.sdfbuilder.sensor import Sensor as SdfSensor
from revolve.sdfbuilder.math import Vector3
from revolve.sdfbuilder.structure import Box, Mesh

# Revolve imports
from ....build.sdf import BodyPart
from ....build.util import in_grams, in_mm

# Local imports
from .util import ColorMixin

MASS = in_grams(90.0)
WIDTH = in_mm(90)
HEIGHT = in_mm(45)


class CoreComponent(BodyPart, ColorMixin):
    """
    The core component of the robot, basically a box with an IMU sensor.
    """

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        self.link = self.create_component(Box(WIDTH, WIDTH, HEIGHT, MASS), "box",
                                          visual=Mesh("model://rg_robot/meshes/CoreComponent.dae"))

        if not self.conf.disable_sensors:
            # Now we will add the IMU sensor. First, we must
            # create a sensor in SDF. The sensor must have a name which
            # is unique for the robot - `add_sensor` ensures this for us
            # assuming the `prefix` argument is left to its default.
            imu = SdfSensor("imu_sensor", "imu", update_rate=self.conf.sensor_update_rate)
            self.link.add_sensor(imu)

        self.apply_color()

    def get_slot(self, slot):
        """
        There's only one slot, return the link.
        :param slot:
        """
        self.check_slot(slot)
        return self.link

    def get_slot_position(self, slot):
        """
        Return slot position
        :param slot:
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
        :param slot:
        """
        return self.get_slot_position(slot).normalized()

    def get_slot_tangent(self, slot):
        """
        Return slot tangent
        :param slot:
        """
        self.check_slot(slot)

        # The top face is tangent to all supported
        # slots in the plane, front, back, right, left
        # Since there's no particular reason for choosing any
        # other we just return the top face for all.
        return Vector3(0, 0, 1)
