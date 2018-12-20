from __future__ import print_function
from __future__ import absolute_import
import sys
from .element import Element
from .math import Vector3, Quaternion, RotationMatrix
from .util import number_format as nf


class Pose(Element):
    """
    An SDF "pose" element, which is an x, y, z position
    plus a roll, pitch, yaw.
    """

    TAG_NAME = 'pose'

    def __init__(self, position=None, rotation=None, **kwargs):
        """
        """
        super(Pose, self).__init__(**kwargs)

        # Zero position and identity rotation
        self.position = Vector3() if position is None else position
        self.rotation = Quaternion() if rotation is None else rotation

    def render_body(self):
        """
        :return:
        """
        body = super(Pose, self).render_body()
        roll, pitch, yaw = self.rotation.get_rpy()
        x, y, z = self.position.x, self.position.y, self.position.z

        body += "%s %s %s %s %s %s" % (nf(x), nf(y), nf(z),
                                       nf(roll), nf(pitch), nf(yaw))

        return body


class Posable(Element):
    """
    Posable is a base class for elements with a name
    and a pose.
    """

    # Whether the pose for this element is in the parent frame
    # or not. A joint, for instance, has a pose, but it is
    # expressed in the child link frame. A parent posable
    # can use this property to decide not to affect this
    # element with transformations.
    PARENT_FRAME = True

    # It might be desirable to have posable functionality without
    # rendering a pose tag (in a compound geometry for instance).
    # In this case, set this to false in subclasses.
    RENDER_POSE = True

    def __init__(self, name, pose=None, **kwargs):
        """
        :param name:
        :type name: str
        :param pose: Initial pose, origin with zero rotation
                     if not specified.
        :type pose: Pose
        :param kwargs:
        :return:
        """
        super(Posable, self).__init__(**kwargs)

        self._pose = Pose() if pose is None else pose
        self.name = name

    def set_pose(self, pose):
        """
        Shortcut call over `set_position` and `set_rotation` for
        a given pose.
        :param pose:
        :type pose: Pose
        :return:
        """
        self.set_position(pose.position)
        self.set_rotation(pose.rotation)

    def set_rotation(self, rotation):
        """
        :type rotation: Quaternion
        :param rotation: Rotation Quaternion
        :return:

        """
        self._pose.rotation = rotation.copy()

    def get_rotation(self):
        """
        Return the rotation quaternion of this posable's pose
        :return:
        :rtype: Quaternion
        """
        return self._pose.rotation.copy()

    def set_position(self, position):
        """
        :type position: Vector3
        :param position:
        :return:
        """
        self._pose.position = position.copy()

    def get_position(self):
        """
        Return the 3-vector position of this posable's pose
        :return:
        :rtype: Vector3
        """
        return self._pose.position.copy()

    def get_pose(self):
        """
        :return: Pose object. Warning: this is not a copy.
        :rtype: Pose
        """
        return self._pose

    def translate(self, translation):
        """
        :type translation: Vector3
        :param translation:
        :return:
        """
        self.set_position(self.get_position() + translation)

    def rotate(self, rotation):
        """
        :type rotation: Quaternion
        :param rotation:
        :return:
        """
        self.set_rotation(rotation * self.get_rotation())

    def render_attributes(self):
        """
        Adds name to the render attributes
        :return:
        :rtype: dict
        """
        attrs = super(Posable, self).render_attributes()

        if self.name is not None:
            attrs.update({"name": self.name})

        return attrs

    def render_elements(self):
        """
        Adds _pose to the render elements
        :return:
        :rtype: list
        """
        pose = self.get_pose()
        elmns = [pose] if self.RENDER_POSE and pose else []
        return elmns + super(Posable, self).render_elements()

    def rotate_around(self, axis, angle, relative_to_child=True):
        """
        Rotates this posable `angle` degrees around the given
        directional vector.
        :param axis:
        :type axis: Vector3
        :param angle:
        :type angle: float
        :param relative_to_child: If true, the axis is expressed in the
                                  child frame.
        :type relative_to_child: bool
        :return:
        """
        if relative_to_child:
            axis = self.to_parent_direction(axis)

        quat = Quaternion.from_angle_axis(angle, axis)
        self.rotate(quat)

    def to_parent_direction(self, vec):
        """
        Returns the given direction vector / rotation quaternion relative to the parent frame.
        :param vec: Vector or quaternion in the local frame
        :type vec: Vector3|Quaternion
        :return:
        :rtype: Vector3|Quaternion
        """
        return self.get_rotation() * vec

    def to_local_direction(self, vec):
        """
        Returns the given direction vector / rotation quaternion relative to the local frame
        :param vec: Direction vector or orientation in the parent frame
        :type vec: Vector3|Quaternion
        :return:
        :rtype: Vector3|Quaternion
        """
        return self.get_rotation().conjugated() * vec

    def to_parent_frame(self, point):
        """
        Returns the given point relative to the parent frame
        :param point: Point in the local frame
        :type point: Vector3
        :return:
        :rtype: Vector3
        """
        pos = self.get_position()
        return self.to_parent_direction(point) + pos

    def to_local_frame(self, point):
        """
        Returns the given point relative to the local frame
        :param point: Point in the parent frame
        :type point: Vector3
        :return:
        :rtype: Vector3
        """
        rot = self.get_rotation().conjugated()
        pos = self.get_position()
        return rot * (point - pos)

    def to_sibling_frame(self, point, sibling):
        """
        Takes a point and converts it to the frame of a sibling
        :param point:
        :type point: Vector3
        :param sibling:
        :type sibling: Posable
        :return: The point in the sibling's frame
        :rtype: Vector3
        """
        # Do this the easy way: convert to parent, then
        # back to sibling
        in_parent = self.to_parent_frame(point)
        return sibling.to_local_frame(in_parent)

    def to_sibling_direction(self, vec, sibling):
        """
        Returns the given direction vector / orientation quaternion
        relative to the frame of a sibling
        :param vec: Direction vector / orientation quaternion in the child frame
        :type vec: Vector3|Quaternion
        :param sibling: The sibling posable
        :type sibling: Posable
        :return:
        :rtype: Vector3|Quaternion
        """
        in_parent = self.to_parent_direction(vec)
        return sibling.to_local_direction(in_parent)

    def align(self, my, my_normal, my_tangent, at,
              at_normal, at_tangent, of, relative_to_child=True):
        """
        Rotates and translates this posable, such that the
        ends of the vectors `my` and `at` touch, aligning
        such that `my_normal` points in the opposite direction of `at_normal`
        and `my_tangent` and `at_tangent` align.

        The two posables need to be in the same parent frame
        for this to work.

        You can choose to specify the positions and orientations either in the parent
        frame or in the child frame using the final argument to this method.
        Be aware that representing orientation vectors in the parent frame
        merely means that they are already rotated with respect to their parent,
        not translated.
        :param my:
        :type my: Vector3
        :param my_normal:
        :type my_normal: Vector3
        :param my_tangent:
        :type my_tangent: Vector3
        :param at:
        :type at: Vector3
        :param at_normal:
        :type at_normal: Vector3
        :param at_tangent:
        :type at_tangent: Vector3
        :param of:
        :type of: Posable
        :param relative_to_child:
        :type relative_to_child: bool
        :return:
        """
        if not my_normal.orthogonal_to(my_tangent):
            raise ValueError("`my_normal` and `my_tangent` should be orthogonal.")

        if not at_normal.orthogonal_to(at_tangent):
            raise ValueError("`at_normal` and `at_tangent` should be orthogonal.")

        # Convert all vectors to local frame if not currently there,
        # we will need this as reference after rotation.
        if not relative_to_child:
            my = self.to_local_frame(my)
            my_normal = self.to_local_direction(my_normal)
            my_tangent = self.to_local_direction(my_tangent)

            at = of.to_local_frame(at)
            at_normal = of.to_local_direction(at_normal)
            at_tangent = of.to_local_direction(at_tangent)

        # This explains how to do the alignment easily:
        # http://stackoverflow.com/questions/21828801/how-to-find-correct-rotation-from-one-vector-to-another

        # We define coordinate systems in which "normal", "tangent" and "normal x tangent" are
        # the x, y and z axes ("normal x tangent" is the cross product). We then determine two
        # rotation matrices, one for the rotation of the standard basis to "my" (R1):
        my_x = my_normal.normalized()
        my_y = my_tangent.normalized()
        my_z = my_x.cross(my_y)

        # Note that we are going to determine an absolute rotation, so we need the vectors
        # in the local frame rather than in the parent frame. We also determine a rotation
        # matrix for the rotation of "at" (R2):
        at_x = of.to_parent_direction(-at_normal).normalized()
        at_y = of.to_parent_direction(at_tangent).normalized()
        at_z = at_x.cross(at_y)

        # For which we do use the parent frame.
        # We now want to provide the rotation matrix from R1 to R2.
        # The easiest way to visualize this is if we first perform
        # the inverse rotation from R1 back to the standard basis,
        # and then rotate to R2.
        r1 = RotationMatrix()
        r2 = RotationMatrix()

        # Warning: `RotationMatrix` is a Matrix4 that can potentially
        # do translations. We want to assign the first block of
        # these matrices only. Syntax is numpy arrays.
        r1[:3, 0], r1[:3, 1], r1[:3, 2] = my_x, my_y, my_z
        r2[:3, 0], r2[:3, 1], r2[:3, 2] = at_x, at_y, at_z

        # The columns of r1 are orthonormal, so we can simply
        # transpose the matrix to get the inverse rotation
        r1.transpose()

        # The final rotation is the inverse of r1, followed by r2
        # (left multiplication)
        """:type : RotationMatrix"""
        rotation = r2 * r1
        self.set_rotation(rotation.get_quaternion())

        my_parent_normal = self.to_parent_direction(my_normal)
        at_parent_normal = of.to_parent_direction(-at_normal)
        if not my_parent_normal.parallel_to(at_parent_normal):
            print("Vector angle: %f" % my_parent_normal.angle(at_parent_normal), file=sys.stderr)
            assert False, "Normal vectors failed to align!"

        parent_tangent = self.to_parent_direction(my_tangent)
        at_parent_tangent = of.to_parent_direction(at_tangent)
        if not parent_tangent.parallel_to(at_parent_tangent):
            print("Vector angle: %f" % parent_tangent.angle(at_parent_tangent), file=sys.stderr)
            assert False, "Tangent vectors failed to align!"

        # Finally, translate so that `my` lands at `at`
        my_pos = self.to_parent_frame(my)
        at_pos = of.to_parent_frame(at)
        translation = at_pos - my_pos
        self.translate(translation)


class PosableGroup(Posable):
    """
    A PosableGroup allows grouping a set of posables with the same parent
    without introducing a new coordinate frame (i.e. without putting
    them inside a link or a model). This lets you conveniently move
    the items within the group together, whilst their position remains
    relative to the groups parent.
    """

    # We don't want to render outer posable group
    TAG_NAME = None

    # Do not render the `Pose` element
    RENDER_POSE = False

    def __init__(self, name=None, pose=None, **kwargs):
        """
        Overrides init to make name optional, it is not useful
        for posable groups.
        :param name:
        :type name: str
        :param pose:
        :type pose: Pose
        :param kwargs:
        :return:
        """
        super(PosableGroup, self).__init__(name=name, pose=pose, **kwargs)

    def set_position(self, position):
        """
        Sets the position of this posable group, translating all the
        posables within it.

        :param position:
        :type position: Vector3
        :return:
        """
        translation = position - self.get_position()

        # Get posables from the element list. It is good practice
        # to only have posables here, but we can easily make sure.
        posables = self.get_affected_posables()

        for posable in posables:
            posable.translate(translation)

        # Store root position
        super(PosableGroup, self).set_position(position)

    def get_affected_posables(self):
        """
        Returns all sub elements which are posable and have their
        pose in the parent frame.
        :return:
        """
        return [posable for posable in self.elements
                if isinstance(posable, Posable) and posable.PARENT_FRAME]

    def set_rotation(self, rotation):
        """
        Set the rotation of this posable group, moving all the posables
        within it accordingly.

        :param rotation:
        :type rotation: Quaternion
        :return:
        """
        root_position = self.get_position()
        inv_rotation = self.get_rotation().conjugated()

        posables = self.get_affected_posables()
        for posable in posables:
            # Get the position and rotation of the child relative
            # to this posable's root (i.e. as if the posable was in [0, 0]
            # with no rotation)
            orig_position = inv_rotation * (posable.get_position() - root_position)

            # The original rotation follows from multiplying the child's rotation
            # with this group's inverse rotation
            orig_rotation = inv_rotation * posable.get_rotation()

            # New position means rotating the original point according to the new
            # rotation, and adding the current position
            new_position = (rotation * orig_position) + root_position

            # New rotation is acquired by multiplying the new rotation
            # with the existing rotation
            new_rotation = rotation * orig_rotation

            posable.set_position(new_position)
            posable.set_rotation(new_rotation)

        # We should still store our own root rotation
        super(PosableGroup, self).set_rotation(rotation)