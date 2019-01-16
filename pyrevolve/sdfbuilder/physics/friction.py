from ..element import Element
from ..util import number_format as nf
from ..math import Vector3


class Friction(Element):
    """
    Friction helper element that outputs for both ODE
    and Bullet where applicable.
    """

    TAG_NAME = "friction"

    def __init__(self, friction=None, friction2=None, fdir1=None,
                 slip1=None, slip2=None, rolling_friction=None, **kwargs):
        """

        :param friction1:
        :param friction2:
        :param fdir1:
        :type fdir1: Vector3
        :param slip1:
        :param slip2:
        :param rolling_friction:
        :return:
        """
        super(Friction, self).__init__(**kwargs)

        self.friction = friction
        self.friction2 = friction2
        self.fdir1 = fdir1
        self.slip1 = slip1
        self.slip2 = slip2
        self.rolling_friction = rolling_friction

        # Elements to be rendered for ODE / Bullet; custom elements
        # can simply be added here.
        self.ode_elements = []
        self.bullet_elements = []

    def render_elements(self):
        """
        Add ODE / Bullet elements to the elements to render.
        :return:
        """
        elements = super(Friction, self).render_elements()

        ode = Element(tag_name="ode")
        ode.add_elements(self.ode_elements)
        bullet = Element(tag_name="bullet")
        bullet.add_elements(self.bullet_elements)

        if self.friction is not None:
            f1 = nf(self.friction)
            ode.add_element("<mu>{}</mu>\n".format(f1))
            bullet.add_element("<friction>{}</friction>\n".format(f1))

        if self.friction2 is not None:
            f2 = nf(self.friction2)
            ode.add_element("<mu2>{}</mu2>\n".format(f2))
            bullet.add_element("<friction2>{}</friction2>\n".format(f2))

        if self.fdir1 is not None:
            x, y, z = self.fdir1
            fdir = "{} {} {}".format(nf(x), nf(y), nf(z))
            ode.add_element("<fdir1>{}</fdir1>\n".format(fdir))
            bullet.add_element("<fdir1>{}</fdir1>\n".format(fdir))

        if self.slip1 is not None:
            ode.add_element("<slip1>{}</slip1>\n".format(nf(self.slip1)))

        if self.slip2 is not None:
            ode.add_element("<slip2>{}</slip2>\n".format(nf(self.slip2)))

        if self.rolling_friction is not None:
            bullet.add_element(
                    element="<rolling_friction>{}</rolling_friction>\n".format(
                              nf(self.rolling_friction)))

        if len(ode.elements):
            elements.append(ode)

        if len(bullet.elements):
            elements.append(bullet)

        return elements