from __future__ import absolute_import
from __future__ import print_function

import sys

# Revolve imports
from ....build.sdf import Box
from ....build.util import in_grams, in_mm

# SDF builder imports
from sdfbuilder.math import Vector3
from sdfbuilder.sensor import Sensor as SdfSensor
from sdfbuilder.util import number_format as nf

# Local imports
from .util import ColorMixin

MASS = in_grams(2)
SENSOR_BASE_WIDTH = in_mm(34)
SENSOR_BASE_THICKNESS = in_mm(1.5)


class LightSensor(Box, ColorMixin):
    """
    Simple light sensor. This extends `Box` for convenience,
    make sure you set the arity to 1 in the body specification.
    """

    def _initialize(self, **kwargs):
        """
        :param kwargs:
        :return:
        """
        self.mass = MASS
        self.x = SENSOR_BASE_THICKNESS
        self.y = self.z = SENSOR_BASE_WIDTH
        super(LightSensor, self)._initialize(**kwargs)

        # Add the SDF camera sensor
        camera = SdfSensor(
                name="{}_light_sensor".format(self.id),
                sensor_type="camera",
                update_rate=self.conf.sensor_update_rate)

        # TODO: Set field of view
        cam_details = "<camera>" \
                      "<image>" \
                      "<width>1</width><height>1</height>" \
                      "</image>" \
                      "<clip><near>{}</near><far>{}</far></clip>" \
                      "</camera>".format(nf(in_mm(1)), nf(in_mm(50000)))
        camera.add_element(cam_details)
        camera.set_position(Vector3(0.5 * self.x, 0, 0))
        self.component.add_sensor(camera, "light")

        if self.conf.visualize_sensors:
            camera.add_element("<visualize>1</visualize>")

        self.apply_color()

    def get_slot_position(self, slot):
        self.check_slot(slot)
        return Vector3(-0.5 * SENSOR_BASE_THICKNESS, 0, 0)

    def get_slot_tangent(self, slot):
        self.check_slot(slot)
        return Vector3(0, 1, 0)
