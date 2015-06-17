from sdfbuilder import Posable, Joint, Link

class ComponentJoint(Posable):
    """
    Since we're constructing robots out of conceptual components (which
    are not actually SDF body parts), we need a way of joint creation
    that is not the SDF joint (since this joins links concretely).
    This is what this class is for. It can be instantiated and positioned
    like a regular SDF joint, only it has some magic regarding its
    final positioning when used in an actual link. Any elements added
    to this joint are also added to the finally created joint.
    """

    # Like the normal joint, this joint should not be moved with
    # its parent.
    PARENT_FRAME = False

    def __init__(self, joint_type, parent, child, pose=None, axis=None,
                 axis2=None, name=None, after_create=None, **kwargs):
        """
        :param joint_type: Type of the joint
        :param parent: Parent component
        :type parent: Component
        :param child:
        :type child: Component
        :param axis: Joint axis 1, in the child component frame as expected
        :param axis2: Joint axis 2 (if applicable) in the child component
        :param after_create:
        :return:
        """
        super(ComponentJoint, self).__init__("", pose=pose)
        self.after_create = after_create
        self.parent = parent
        self.child = child
        self.type = joint_type
        self.axis, self.axis2 = axis, axis2
        self.created_joint = None
        self.kwargs = kwargs
        self.name = name

    def create_joint(self, parent_link, child_link, parent, child):
        """
        Creates the actual joint given the information in this class
        and the desired parent / child links.

        :param parent_link:
        :type parent_link: Link
        :param child_link:
        :type child_link: Link
        :param parent: The positioned parent sub element
        :type parent: Posable
        :param child: The positioned child sub element
        :type child: Posable
        :return:
        """
        joint = Joint(self.type, parent_link, child_link, axis=self.axis, axis2=self.axis2,
                      name=self.name, **self.kwargs)

        # Translate the joint with the child. Afterwards we need only to rotate
        # the joint with the child (i.e. set it's rotation in the parent frame
        # relative to the child) and then we need not modify the axes (!!).
        position = child.to_parent_frame(self.get_position())
        rotation = child.to_parent_direction(self.get_rotation())
        joint.set_position(position)
        joint.set_rotation(rotation)

        if self.after_create:
            self.after_create(joint, parent_link, child_link, parent, child)

        self.created_joint = joint
        return joint
