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
            ode.add_element("<mu>%s</mu>" % f1)
            bullet.add_element("<friction>%s</friction>" % f1)

        if self.friction2 is not None:
            f2 = nf(self.friction2)
            ode.add_element("<mu2>%s</mu2>" % f2)
            bullet.add_element("<friction2>%s</friction2>" % f2)

        if self.fdir1 is not None:
            x, y, z = self.fdir1
            fdir = "%s %s %s" % (nf(x), nf(y), nf(z))
            ode.add_element("<fdir1>%s</fdir1>" % fdir)
            bullet.add_element("<fdir1>%s</fdir1>" % fdir)

        if self.slip1 is not None:
            ode.add_element("<slip1>%s</slip1>" % nf(self.slip1))

        if self.slip2 is not None:
            ode.add_element("<slip2>%s</slip2>" % nf(self.slip2))

        if self.rolling_friction is not None:
            bullet.add_element("<rolling_friction>%s</rolling_friction>" % nf(self.rolling_friction))

        if len(ode.elements):
            elements.append(ode)

        if len(bullet.elements):
            elements.append(bullet)

        return elements