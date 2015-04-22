from sdfbuilder.base import PosableGroup, Link
from sdfbuilder.joint import FixedJoint, Axis
from sdfbuilder.math import Vector3
from .exception import ArityException


class BodyPart(PosableGroup):
    """
    Base component class
    """
    # Default arity for classes of this type
    ARITY = 0

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
        self.arity = self.ARITY

        # Call child initialization function
        self._initialize(**kwargs)

    def _initialize(self, **kwargs):
        """
        Initializes the component, to be implemented by child model.
        :return:
        """
        raise NotImplementedError("`BodyPart._initialize()` must be implemented by child class.")

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

    def fix_links(self, parent, child, anchor, axis):
        """
        Connects two links using a joint.
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
        # TODO Implement
        raise NotImplementedError("Must implement.")

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
            self.rotate_around(a_normal, orientation)

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

    def check_slot(self, slot):
        """
        Checks whether the given slot is valid, raises an
        ArityException when it is not.
        :param slot:
        :type slot: int
        :return:
        """
        if slot < 0 or slot >= self.arity:
            raise ArityException("Invalid slot %d for body part." % slot)