from ..link import Link
from ..posable import Posable
from ..element import Element
from ..math import Vector3
from ..util import number_format as nf


class Joint(Posable):
    """
    Joint base class, though using the base class should
    suffice for most uses.
    """
    # Joint tag name
    TAG_NAME = "joint"

    # Joint has a pose, but it is not in the parent frame
    PARENT_FRAME = False

    def __init__(self, joint_type, parent, child, pose=None, axis=None, axis2=None, name=None, **kwargs):
        """
        :param axis:
        :param axis2:
        :param joint_type:
        :type joint_type: str
        :param parent:
        :type parent: Link
        :param child:
        :type child: Link
        :param name:
        :param kwargs:
        :return:
        """
        if name is None:
            name = "joint_"+parent.name+"_"+child.name

        super(Joint, self).__init__(name=name, pose=pose, **kwargs)

        self.parent = parent
        self.child = child
        self.type = joint_type

        if isinstance(axis, Vector3):
            axis = Axis(axis=axis)

        if isinstance(axis2, Vector3):
            axis2 = Axis(axis=axis2, tag_name='axis2')

        self.axis = Axis() if axis is None else axis
        self.axis2 = axis2

    def render_elements(self):
        """
        Adds joint elements to be rendered
        """
        elements = ["<parent>"+self.parent.name+"</parent>",
                    "<child>"+self.child.name+"</child>",
                    self.axis]

        if self.axis2 is not None:
            self.axis2.tag_name = 'axis2'
            elements.append(self.axis2)

        return super(Joint, self).render_elements() + elements

    def render_attributes(self):
        """
        Add type to the attributes to be rendered
        """
        attrs = super(Joint, self).render_attributes()
        attrs['type'] = self.type
        return attrs


class Axis(Element):
    """
    Defines a joint axis
    """
    # Note that this might just as well be used for
    # an axis2, just override the property in init.
    TAG_NAME = "axis"

    def __init__(self, axis=None, limit=None, use_parent_model_frame=False, **kwargs):
        """
        :param axis:
        :type axis: Vector3
        :param limit:
        :type limit: Limit
        :param use_parent_model_frame:
        :type use_parent_model_frame: bool
        """
        super(Axis, self).__init__(**kwargs)

        if axis is None:
            axis = Vector3(1, 0, 0)

        self.axis = axis.normalized()
        self.limit = limit
        self.use_parent_model_frame = use_parent_model_frame

    def render_elements(self):
        """
        Add xyz and limit elements
        """
        elements = super(Axis, self).render_elements()

        x, y, z = self.axis.x, self.axis.y, self.axis.z
        xyz = "<xyz>%s %s %s</xyz>" % (nf(x), nf(y), nf(z))
        elements += [xyz, "<use_parent_model_frame>%d</use_parent_model_frame>" % self.use_parent_model_frame]

        if self.limit:
            elements.append(self.limit)

        return elements


class Limit(Element):
    """
    Defines a joint axis limit
    """
    # Limit tag name
    TAG_NAME = "limit"

    def __init__(self, lower=None, upper=None, effort=None, velocity=None,
                 stiffness=None, dissipation=None, **kwargs):
        """
        :param lower:
        :param upper:
        :param effort:
        :param velocity:
        :param stiffness:
        :param dissipation:
        :return:
        """
        super(Limit, self).__init__(**kwargs)

        self.lower = lower
        self.upper = upper
        self.effort = effort
        self.velocity = velocity
        self.stiffness = stiffness
        self.dissipation = dissipation

    def render_elements(self):
        """
        Add local properties to the elements to be rendered.
        :return:
        """
        elements = super(Limit, self).render_elements()

        for attr in ['lower', 'upper', 'effort', 'velocity', 'stiffness', 'dissipation']:
            val = getattr(self, attr, None)
            if val is not None:
                elements.append("<%s>%s</%s>" % (attr, nf(val), attr))

        return elements