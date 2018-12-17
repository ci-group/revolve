from __future__ import absolute_import

from pyrevolve.sdfbuilder import Element
from pyrevolve.sdfbuilder.util import number_format as nf


class BasicBattery(Element):
    """
    The rv:battery element, to be included in a robot's plugin
    """
    TAG_NAME = 'rv:battery'

    def __init__(self, level):
        """

        :param level: Initial battery level
        :type level: float
        :return:
        """
        super(BasicBattery, self).__init__()
        self.level = level

    def render_elements(self):
        """

        :return:
        """
        elms = super(BasicBattery, self).render_elements()
        return elms + [Element(tag_name="rv:level", body=nf(self.level))]
