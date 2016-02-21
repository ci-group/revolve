"""
The rv:battery element, to be included in a robot's plugin
"""
from sdfbuilder import Element
from sdfbuilder.util import number_format as nf


class BasicBattery(Element):
    """

    """
    TAG_NAME = 'rv:battery'

    def __init__(self, level, discharge_rate):
        """

        :param level:
        :type level: float
        :param discharge_rate:
        :type discharge_rate: float
        :return:
        """
        super(Battery, self).__init__()

        self.level = level
        self.discharge_rate = discharge_rate

    def render_elements(self):
        """

        :return:
        """
        elms = super(BasicBattery, self).render_elements()
        return elms + [
            Element(tag_name="rv:level", body=nf(self.level)),
            Element(tag_name="rv:discharge_rate", body=nf(self.discharge_rate))
        ]
