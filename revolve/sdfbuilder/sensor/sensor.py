from ..posable import Posable
from ..element import Element
from ..util import number_format as nf


class Sensor(Posable):
    """
    Sensor base class, using the base class should
    suffice in most cases since writing the XML is
    just as easy.
    """
    # Sensor tag name
    TAG_NAME = "sensor"

    def __init__(self, name, sensor_type, pose=None, update_rate=None, always_on=True, **kwargs):
        """
        :param name:
        :param sensor_type:
        :param pose:
        :param update_rate:
        :param always_on:
        :param kwargs:
        """
        super(Sensor, self).__init__(name, pose, **kwargs)
        self.update_rate = update_rate
        self.always_on = always_on
        self.type = sensor_type

    def render_attributes(self):
        """
        Add type to the attributes to be rendered
        """
        attrs = super(Sensor, self).render_attributes()
        attrs['type'] = self.type
        return attrs

    def render_elements(self):
        """
        :return:
        """
        els = []
        if self.update_rate is not None:
            els.append(Element(tag_name="update_rate", body=nf(self.update_rate)))

        if self.always_on is not None:
            els.append(Element(tag_name="always_on", body="1" if self.always_on else "0"))

        return super(Sensor, self).render_elements() + els
