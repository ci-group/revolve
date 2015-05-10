from sdfbuilder import PosableGroup, Link, Model
from sdfbuilder.joint import Joint, FixedJoint
from sdfbuilder.math import Vector3

from revolve.builder.sdf.body.exception import ArityException


class BodyPart(PosableGroup):
    """
    Base component class
    """

    def __init__(self, id, conf, **kwargs):
        """

        :param id:
        :type id: string
        :param conf:
        :return:
        """
        super(BodyPart, self).__init__(None, **kwargs)
        self.id = id
        self.conf = conf

        # Specifying arity through arguments is optional. Since the arity
        # is defined in the spec, there is usually no need to set it
        # in the body part itself.
        self.arity = kwargs.get('arity', None)

        # Since body parts do not have direct access to the model, they
        # must list joints separately. They can be added to this list.
        self.joints = []

        # Ordered list of motors that this body part implements. These
        # motors will be rendered to the SDF plugin.
        self.motors = []

        # Ordered list of sensors in the body part. These sensors
        # will be rendered to the SDF plugin.
        self.sensors = []

        # Call child initialization function
        self._initialize(**kwargs)

    def _initialize(self, **kwargs):
        """
        Initializes the component, to be implemented by child model.
        :return:
        """
        raise NotImplementedError("`BodyPart._initialize()` must be implemented by child class.")

    def make_color(self, r, g, b, a=1.0):
        """
        Applies `make_color` with the given arguments to every
        link in this body part.
        :param r:
        :param g:
        :param b:
        :param a:
        :return:
        """
        for link in self.get_elements_of_type(Link):
            link.make_color(r, g, b, a)

    def get_slot(self, slot_id):
        """
        Returns the link for the given slot ID
        :param slot_id: Slot ID
        :type slot_id: int
        :return: Link for given slot ID
        :rtype: Link
        """
        raise NotImplementedError("`BodyPart.get_slot()` not implemented.")

    def get_slot_position(self, slot_id):
        """
        Returns the position of the given slot ID in this component's frame
        :param slot_id: Slot ID
        :type slot_id: int
        :return: Position for given slot ID in child coordinates
        :rtype: Vector3
        """
        raise NotImplementedError("`BodyPart.get_slot_position()` not implemented.")

    def get_slot_normal(self, slot_id):
        """
        Returns the normal direction vector of the given slot ID in this component's frame
        :param slot_id: Slot ID
        :type slot_id: int
        :return: Normal direction vector of the given slot ID in this component's frame
        :rtype: Vector3
        """
        raise NotImplementedError("`BodyPart.get_slot_normal()` not implemented.")

    def get_slot_tangent(self, slot_id):
        """
        Returns the vector that represents the given slot's zero orientation, which should be
        tangent to the slot normal.
        :param slot_id: Slot ID
        :type slot_id: int
        :return: Slot tangent vector
        :rtype: Vector3
        """
        raise NotImplementedError("`BodyPart.get_slot_tangent()` not implemented.")

    def create_link(self, label=None):
        """
        :param label:
        :type label: int
        :return:
        """
        append = "__"+str(len(self.elements)) if label is None else "_"+str(label)
        link = Link("link_"+str(id)+"_"+append)
        self.add_element(link)

    def attach(self, other, other_slot, my_slot, orientation):
        """
        :param other:
        :type other: BodyPart
        :param other_slot:
        :type other_slot: int
        :param my_slot:
        :type my_slot: int
        :param orientation: Orientation in radians
        :type orientation: float
        :return:
        """
        a_slot = self.get_slot_position(my_slot)
        b_slot = other.get_slot_position(other_slot)
        a_normal = self.get_slot_normal(my_slot)
        b_normal = other.get_slot_normal(other_slot)
        a_tangent = self.get_slot_tangent(my_slot)
        b_tangent = other.get_slot_tangent(other_slot)

        self.align(
            a_slot,
            a_normal,
            a_tangent,

            b_slot,
            b_normal,
            b_tangent,

            other,
            relative_to_child=True
        )

        if orientation:
            self.rotate_around(a_normal, orientation, relative_to_child=True)

        child = self.get_slot(my_slot)
        parent = other.get_slot(other_slot)

        # We need to specify the joint position in the child frame,
        # but the slot position is in the component frame. Because
        # of the posable group's semantics, the component and the
        # child are actually in the same frame (the component root
        # is an imaginary sibling) so we can use sibling translation.
        anchor = self.to_sibling_frame(a_slot, child)

        # The same thing holds for the joint axis, which is the normal
        axis = self.to_sibling_frame(a_normal, child)

        # Attach with a fixed link
        self.fix_links(parent, child, anchor, axis)

    def add_joint(self, joint):
        """
        Adds a joint to this model
        :param joint:
        :type joint: Joint
        :return:
        """
        self.joints.append(joint)

    def get_joints(self):
        """
        Returns the defined joints for this body part. There is
        usually no need to override this method.
        :return:
        :rtype: list
        """
        return self.joints

    def fix_links(self, parent, child, anchor, axis):
        """
        Creates an immovable joint between the two given links,
        at the given position and around the specified axis. The
        joint is added to this body part's joint list.
        :param parent:
        :type parent: Link
        :param child:
        :type child: Link
        :param anchor:
        :type anchor: Vector3
        :param axis:
        :type axis: Vector3
        :return:
        """
        joint = FixedJoint(parent, child, axis=axis)
        joint.set_position(anchor)
        self.add_joint(joint)

    def get_motors(self):
        """
        :return:
        :rtype: list
        """
        return self.motors

    def get_sensors(self):
        """
        :return:
        :rtype: list
        """
        return self.sensors

    def check_slot(self, slot):
        """
        Checks whether the given slot is valid, raises an
        ArityException when it is not.
        :param slot:
        :type slot: int
        :return:
        """
        assert self.arity is not None, "Arity of body part was not set, " \
                                       "make sure your builder derives this from the spec."

        if slot < 0 or slot >= self.arity:
            raise ArityException("Invalid slot %d for body part." % slot)