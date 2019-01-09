from __future__ import absolute_import

from pyrevolve.sdfbuilder import Element, Link
from pyrevolve.sdfbuilder.sensor import Sensor as SdfSensor
from pyrevolve.sdfbuilder.util import number_format as nf


class Sensor(Element):
    """
    Plugin sensor base class. This is used to communicate sensor
    configuration through the SDF plugin to the model controller
    in Gazebo.
    """
    # SDF tag name, should not be changed in subclass
    TAG_NAME = 'rv:sensor'

    def __init__(self, part_id, link, sensor, sensor_type=None):
        """
        :param link:
        :type link: Link
        :param part_id: ID of the part this sensor belongs to, required to identify
                        the corresponding input neuron(s).
        :type part_id: str
        :param sensor: SDF element for this sensor, or a `VirtualSensor` instance
                       if applicable.
        :type sensor: SdfSensor|VirtualSensor
        :param sensor_type: Type of the sensor. Defaults to the type of the given SDF sensor,
                            but it can be overridden to communicate loading a different sensor
                            handler.
        :type sensor_type: str
        :return:
        """
        super(Sensor, self).__init__()
        self.link = link
        self.type = sensor_type if sensor_type is not None else sensor.type
        self.is_virtual = getattr(sensor, 'is_virtual', False)
        self.sensor = sensor
        self.part_id = part_id

    def render_attributes(self):
        """
        Adds default sensor attributes before render.
        """
        attrs = super(Sensor, self).render_attributes()

        attrs.update({
            'link': self.link.name,
            'part_id': self.part_id,
            'type': self.type,
            'id': '{}__{}'.format(self.part_id, self.sensor.name)
        })

        # Sensor may be virtual, so have optional Gazebo sensor reference
        if not self.is_virtual:
            attrs['sensor'] = self.sensor.name

        return attrs

    def render_elements(self):
        """
        :return:
        """
        elmns = super(Sensor, self).render_elements()
        if self.is_virtual:
            elmns.append(self.sensor)

        return elmns


class VirtualSensor(Element):
    """
    The virtual sensor can be used for sensors that don't have
    actual SDF / Gazebo counterparts but will be loaded as sensor
    plugins in Revolve robot controllers. A battery sensor is a
    good example of this.

    Virtual sensor elements are rendered as part of their `rv:sensor`
    tag in the plugin rather than as sensor elements in the component's
    link.
    """
    TAG_NAME = 'rv:virtual_sensor'

    def __init__(self, name, sensor_type):
        """

        :param name:
        :param part_id:
        :param sensor_type:
        :return:
        """
        super(VirtualSensor, self).__init__()

        self.is_virtual = True

        self.name = name
        self.type = sensor_type


class BasicBatterySensor(VirtualSensor):
    """
    Basic battery virtual sensor. Only a thin convenience wrapper
    over the `VirtualSensor` class.
    """
    TAG_NAME = 'rv:basic_battery_sensor'

    def __init__(self, name):
        """

        :param name:
        :return:
        """
        super(BasicBatterySensor, self).__init__(name, "basic_battery")


class PointIntensitySensor(VirtualSensor):
    """
    The point proximity sensor returns the Euclidean distance from
    the center of mass of the robot to some predefined point,
    altered by some function.
    """
    TAG_NAME = 'rv:point_intensity_sensor'

    def __init__(self, name, point, i_max=1.0, r=1.0):
        """
        Point proximity sensor with defined point and function
        coefficients a, b, c, which are used to determine the sensor
        values as:

        b * (a * distance)^c

        :param name:
        :param a:
        :param b:
        :param c:
        :return:
        """
        super(PointIntensitySensor, self).__init__(name, "point_intensity")
        self.point = point
        self.i_max = i_max
        self.r = r

    def render_elements(self):
        """

        :return:
        """
        elmns = super(PointIntensitySensor, self).render_elements()
        return elmns + [
            Element(tag_name='rv:point',
                    body='{}'.format(tuple(self.point))),
            Element(tag_name='rv:function',
                    attributes={'i_max': self.i_max, 'r': self.r})
        ]
