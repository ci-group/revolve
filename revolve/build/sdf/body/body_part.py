from sdfbuilder import PosableGroup
from sdfbuilder.math import Vector3, Quaternion
from sdfbuilder.structure import Collision, Visual

from .exception import ArityException
from .component import Component
from .joint import ComponentJoint


class BodyPart(PosableGroup):
    """
    Base body part class. A body part is defined by several things:

    - A set of components, defining visual / collision properties. Components
      are either fixed statically or by a joint, which you can indicate
      with the `self.fix` and `self.add_joint` methods.
    - A set of "slots", which are attachment positions on which this body
      part can be connected to another. Slots are defined by:
      -- The `Component` on which the slot lies, i.e. the component
         the other body part attaches to.
      -- The position of the slot
      -- A vector normal to the slot
      -- A vector tangent to the slot

    When two body parts are connected, their slots' normal vectors are aligned
    in opposite directions, and their slots tangent vectors are aligned to
    determine the zero orientation (after which rotation may be applied for
    another orientation). The slot positions are then translated to touch
    each other to finish alignment of the body parts.

    A body part has a predefined number of slots, as given by the arity
    of the body part. Since this arity is generally stated in the
    `BodyImplementation`, you do not have to define it again in the
    body part (though it might help to state it in a comment).

    In order to implement a `BodyPart`, you must extend this class, and
    implement the following methods:

    - `_initialize`: Build the SDF model in this method. This involves
                     creating all links, joints and sensors, and registering
                     them with the body part.
    - `get_slot(slot)`: Should return the component for the given slot.
    - `get_slot_position(slot)`: Return the x, y, z position of the slot,
                                 in the frame of the body part.
    - `get_slot_normal(slot)`: Return a vector normal to the slot, in the frame
                               of the body part.
    - `get_slot_tangent(slot)`: Return a vector tangent to the slot, in the frame of
                                the body part. This vector should be orthogonal to
                                the normal vector.
    """

    def __init__(self, id, conf, **kwargs):
        """
        Body part constructor. Note that the `BodyPart` constructor does
        not accept a pose - allowing an initial pose would complicate
        body part initialization and is thus disabled.
        :param id:
        :type id: string
        :param conf: A configuration object that can be passed around
                     by your construction mechanism.
        :return:
        """
        super(BodyPart, self).__init__(None, **kwargs)
        self.id = id
        self.conf = conf

        # Specifying arity through arguments is optional. Since the arity
        # is defined in the spec, there is usually no need to set it
        # in the body part itself.
        self.arity = kwargs.get('arity', None)

        # List of components which have been added thusfar
        self.components = []

        # Ordered list of motors that this body part implements. These
        # motors will be rendered to the SDF plugin.
        self.motors = []

        # Store the dictionary of arguments so other
        # functions can access it.
        self.part_params = kwargs

        # Call child initialization function
        self._initialize(**kwargs)

    def _initialize(self, **kwargs):
        """
        Initializes the component, to be implemented by child model.
        :return:
        """
        raise NotImplementedError("`BodyPart._initialize()` must be implemented by child class.")

    def create_component(self, geometry, label=None, collision=True, visual=True):
        """
        :param geometry:
        :param label:
        :return:
        """
        append = "__"+str(len(self.elements)) if label is None else "_"+str(label)
        component = Component(
            self.id,
            "component_"+str(self.id)+"_"+append,
            geometry, collision, visual
        )

        self.add_element(component)
        return component

    def get_components(self):
        """
        Since only `Component`s can be added to a body part,

        :return:
        """
        return self.get_elements_of_type(Component)

    def fix(self, a, b):
        """
        Marks two components as fixed to each other.
        :param a:
        :type a: Component
        :param b:
        :type b: Component
        :return:
        """
        a.create_connection(b)

    def add_joint(self, joint):
        """
        Adds a joint to this model.
        :param joint:
        :type joint: ComponentJoint
        :return:
        """
        joint.parent.create_connection(joint.child, joint)

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
        for visual in self.get_elements_of_type(Visual, recursive=True):
            visual.add_color(r, g, b, a)

    def add_surface_all(self, surface):
        """
        Adds the given surface element to all link collision
        objects in this body part.
        :param surface:
        :return:
        """
        for collision in self.get_elements_of_type(Collision, recursive=True):
            collision.add_element(surface)

    def get_slot(self, slot_id):
        """
        Returns the link for the given slot ID
        :param slot_id: Slot ID
        :type slot_id: int
        :return: Component for the given slot ID
        :rtype: Component
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
        Returns the normal direction vector of the given slot ID in this component's frame.
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

    def attach(self, other, other_slot, my_slot, orientation):
        """
        Positions all the elements in this body part to align slots
        with another body part.

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

        if orientation:
            # Rotate the a_tangent vector over the normal
            # with the given number of radians to apply
            # the rotation. Rotating this vector around
            # the normal should not break their orthogonality.
            rot = Quaternion.from_angle_axis(orientation, a_normal)
            a_tangent = rot * a_tangent

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

        # Internal sanity check
        norm = (self.to_parent_frame(a_slot) - other.to_parent_frame(b_slot)).norm()
        assert norm < 1e-5, "Incorrect attachment positions!"

        my_component = self.get_slot(my_slot)
        at_component = other.get_slot(other_slot)

        # Create a connection between these two slots to complete
        # the body graph.
        at_component.create_connection_one_way(my_component)

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
