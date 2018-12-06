from __future__ import absolute_import

# Revolve imports
from ....build.sdf import Box, Sensor
from ....build.util import in_grams, in_mm

# SDF builder imports
from sdfbuilder.math import Vector3
from sdfbuilder.sensor import Sensor as SdfSensor
from sdfbuilder.structure import Box as BoxGeom, Mesh, Visual

# Local imports
from .util import ColorMixin

MASS = in_grams(3)
SENSOR_BASE_WIDTH = in_mm(34)
SENSOR_BASE_THICKNESS = in_mm(1.5)
SENSOR_THICKNESS = in_mm(9)
SENSOR_WIDTH = in_mm(18.5)
SENSOR_HEIGHT = in_mm(16)
""" Of each left / right sensors """

SEPARATION = in_mm(1)


class TouchSensor(Box, ColorMixin):
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
        x_sensors = 0.5 * (SENSOR_BASE_THICKNESS + SENSOR_THICKNESS)
        y_left_sensor = -0.5 * SENSOR_WIDTH - SEPARATION
        y_right_sensor = 0.5 * SENSOR_WIDTH + SEPARATION

        visual = Visual("touch_visual", Mesh("model://rg_robot/meshes/TouchSensor.dae"))
        visual.translate(Vector3(0.5 * SENSOR_THICKNESS, 0, 0))
        self.component = self.create_component(
            BoxGeom(self.x, self.y, self.z, self.mass), "box",
            visual=visual
        )

        self._sensor_helper("left", x_sensors, y_left_sensor)
        self._sensor_helper("right", x_sensors, y_right_sensor)

        self.apply_color()

    def _sensor_helper(self, label, x_sensors, y_sensor):
        """
        :return:
        """
        # Visual is provided by the mesh in the root
        sensor_component = self.create_component(
            BoxGeom(SENSOR_THICKNESS, SENSOR_WIDTH, SENSOR_HEIGHT, MASS), label,
            visual=False
        )
        sensor_component.set_position(Vector3(x_sensors, y_sensor, 0))

        # Anchor and axis are in child frame
        self.fix(self.component, sensor_component)

        # Create and add the SDF sensor
        contact = SdfSensor(label+"_sensor", "contact",
                            update_rate=self.conf.sensor_update_rate)
        contact.add_element('<contact><collision>'+sensor_component.collision.name+'</collision></contact>')
        sensor_component.add_sensor(contact, "touch")

    def get_slot_position(self, slot):
        self.check_slot(slot)
        # TODO Still seem to have some positioning issues
        return self.component.to_sibling_frame(
            Vector3(-0.5 * SENSOR_BASE_THICKNESS, 0, 0),
            self
        )

    def get_slot_tangent(self, slot):
        self.check_slot(slot)
        return Vector3(0, 1, 0)
