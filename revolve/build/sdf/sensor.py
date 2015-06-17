from sdfbuilder import Element, Link
from sdfbuilder.sensor import Sensor as SdfSensor


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
        :param sensor: SDF element for this sensor
        :type sensor: SdfSensor
        :param sensor_type: Type of the sensor. Defaults to the type of the given SDF sensor,
                            but it can be overridden to communicate loading a different sensor
                            handler.
        :type sensor_type: str
        :return:
        """
        super(Sensor, self).__init__()
        self.link = link
        self.type = sensor_type if sensor_type is not None else sensor.type
        self.sensor = sensor
        self.part_id = part_id

    def render_attributes(self):
        """
        Adds default sensor attributes before render.
        """
        attrs = super(Sensor, self).render_attributes()
        attrs.update({
            'link': self.link.name,
            'sensor': self.sensor.name,
            'part_id': self.part_id,
            'id': '%s__%s' % (self.part_id, self.sensor.name),
            'type': self.type
        })

        return attrs
