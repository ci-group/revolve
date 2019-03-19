import sys
import xml.etree.ElementTree

from pyrevolve import SDF
import pyrevolve.SDF.math


class Pose(xml.etree.ElementTree.Element):
    def __init__(self, position: SDF.math.Vector3 = None, rotation: SDF.math.Quaternion = None):
        super().__init__('pose')
        self.position = SDF.math.Vector3() if position is None else position
        self.rotation = SDF.math.Quaternion() if rotation is None else rotation

    @property
    def text(self):
        x, y, z = self.position.x, self.position.y, self.position.z
        roll, pitch, yaw = self.rotation.get_rpy()

        return "{:e} {:e} {:e} {:e} {:e} {:e}".format(
            x, y, z,
            roll, pitch, yaw,
        )


class Posable(xml.etree.ElementTree.Element):
    def __init__(self, tag, attrib={}, position=None, rotation=None, **extra):
        super().__init__(tag, attrib=attrib, **extra)
        self._pose = Pose(position=position, rotation=rotation)
        self.append(self._pose)

    @property
    def pose(self):
        return self._pose

    @pose.setter
    def pose(self, pose: Pose):
        self.set_position(pose.position)
        self.set_position(pose.position)

    def get_position(self):
        """
        :return: copy of the internal position
        :rtype: SDF.math.Vector3
        """
        return self._pose.position.copy()

    def get_rotation(self):
        """
        :return: copy of the internal rotation
        :rtype: SDF.math.Quaternion
        """
        return self._pose.rotation.copy()

    def set_position(self, position: SDF.math.Vector3):
        self._pose.position = position.copy()

    def set_rotation(self, rotation: SDF.math.Quaternion):
        self._pose.rotation = rotation.copy()

    def translate(self, translation: SDF.math.Vector3):
        self._pose.position = self._pose.position + translation

    def rotate(self, rotation: SDF.math.Quaternion):
        self._pose.rotation = rotation * self._pose.rotation

    def rotate_around(self, axis: SDF.math.Vector3, angle: float, relative_to_child: bool = True):
        """
        Rotates this Posable `angle` degrees around the given directional vector
        :param axis:
        :param angle:
        :param relative_to_child: If True, the axis is expressed in the
                                  child frame.
        :return:
        """
        if relative_to_child:
            axis = self.to_parent_direction(axis)

        quat = SDF.math.Quaternion.from_angle_axis(angle, axis)
        self.rotate(quat)

    def to_parent_direction(self, vec):
        """
        Returns the given direction vector / rotation quaternion relative to
        the parent frame.
        :param vec: Vector or quaternion in the local frame
        :type vec: SDF.math.Vector3|SDF.math.Quaternion
        :return:
        :rtype: SDF.math.Vector3|SDF.math.Quaternion
        """
        return self._pose.rotation * vec

    def to_local_direction(self, vec):
        """
        Returns the given direction vector / rotation quaternion relative to
        the local frame
        :param vec: Direction vector or orientation in the parent frame
        :type vec: SDF.math.Vector3|SDF.math.Quaternion
        :return:
        :rtype: SDF.math.Vector3|SDF.math.Quaternion
        """
        return self._pose.rotation.conjugated() * vec

    def to_parent_frame(self, point: SDF.math.Vector3):
        """
        Returns the given point relative to the parent frame
        :param point: Point in the local frame
        :return:
        :rtype: SDF.math.Vector3
        """
        position = self._pose.position
        return self.to_parent_direction(point) + position

    def to_local_frame(self, point: SDF.math.Vector3):
        """
        Returns the given point relative to the local frame
        :param point: Point in the parent frame
        :return:
        :rtype: SDF.math.Vector3
        """
        rotation = self._pose.rotation.conjugated()
        position = self._pose.position
        return rotation * (point - position)

    def to_sibling_frame(self, point: SDF.math.Vector3, sibling):
        """
        Takes a point and converts it to the frame of a sibling
        :param point:
        :param sibling:
        :type sibling: Posable
        :return: The point in the sibling's frame
        :rtype: SDF.math.Vector3
        """
        # Do this the easy way: convert to parent, then
        # back to sibling
        in_parent = self.to_parent_frame(point)
        return sibling.to_local_frame(in_parent)

    def to_sibling_direction(self, vec, sibling):
        """
        Returns the given direction vector / orientation quaternion relative
        to the frame of a sibling
        :param vec: Direction vector / orientation quaternion in the child frame
        :type vec: SDF.math.Vector3|SDF.math.Quaternion
        :param sibling: The sibling posable
        :type sibling: Posable
        :return:
        :rtype: SDF.math.Vector3|SDF.math.Quaternion
        """
        in_parent = self.to_parent_direction(vec)
        return sibling.to_local_direction(in_parent)

    def align(self,
              my,
              at,
              of,
              relative_to_child: bool = True):
        """
        Rotates and translates this Posable, such that the ends of the
        vectors `my.pos` and `at.pos` touch, aligning such that `my.normal` points in
        the opposite direction of `at.normal` and `my_tangent` and
        `at.tangent` align.

        The two Posables need to be in the same parent frame for this to work.

        You can choose to specify the positions and orientations either in
        the parent frame or in the child frame using the final argument to
        this method. Be aware that representing orientation vectors in the
        parent frame merely means that they are already rotated with respect
        to their parent, not translated.
        :param my: BoxSlot (pos, norm, tang) to move
        :type my: BoxSlot
        :param at: BoxSlot (pos, norm, tang) target where to attach it
        :type at: BoxSlot
        :param of:
        :type of: Posable
        :param relative_to_child:
        :return:
        """
        if not my.normal.orthogonal_to(my.tangent):
            raise ValueError("`my.normal` and `my_tangent` should be orthogonal.")

        if not at.normal.orthogonal_to(at.tangent):
            raise ValueError("`at.normal` and `at.tangent` should be orthogonal.")

        # Convert all vectors to local frame if not currently there,
        # we will need this as reference after rotation.
        if not relative_to_child:
            my.pos = self.to_local_frame(my.pos)
            my.normal = self.to_local_direction(my.normal)
            my.tangent = self.to_local_direction(my.tangent)

            at.pos = of.to_local_frame(at.pos)
            at.normal = of.to_local_direction(at.normal)
            at.tangent = of.to_local_direction(at.tangent)

        # This explains how to do the alignment easily:
        # http://stackoverflow.com/questions/21828801/how-to-find-correct-rotation-from-one-vector-to-another

        # We define coordinate systems in which "normal", "tangent" and
        # "normal x tangent" are the x, y and z axes ("normal x tangent" is
        # the cross product). We then determine two rotation matrices,
        # one for the rotation of the standard basis to "my" (R1):
        my_x = my.normal.normalized()
        my_y = my.tangent.normalized()
        my_z = my_x.cross(my_y)

        # Note that we are going to determine an absolute rotation,
        # so we need the vectors in the local frame rather than in the parent
        #  frame. We also determine a rotation matrix for the rotation of
        # "at" (R2):
        at_x = of.to_parent_direction(-at.normal).normalized()
        at_y = of.to_parent_direction(at.tangent).normalized()
        at_z = at_x.cross(at_y)

        # For which we do use the parent frame. We now want to provide the
        # rotation matrix from R1 to R2. The easiest way to visualize this is
        #  if we first perform the inverse rotation from R1 back to the
        # standard basis, and then rotate to R2.
        r1 = SDF.math.RotationMatrix()
        r2 = SDF.math.RotationMatrix()

        # Warning: `RotationMatrix` is a Matrix4 that can potentially do
        # translations. We want to assign the first block of these matrices
        # only. Syntax is numpy arrays.
        r1[:3, 0], r1[:3, 1], r1[:3, 2] = my_x, my_y, my_z
        r2[:3, 0], r2[:3, 1], r2[:3, 2] = at_x, at_y, at_z

        # The columns of r1 are orthonormal, so we can simply transpose the
        # matrix to get the inverse rotation
        r1.transpose()

        # The final rotation is the inverse of r1, followed by r2
        # (left multiplication)
        rotation = r2 * r1
        self.set_rotation(rotation.get_quaternion())

        my_parent_normal = self.to_parent_direction(my.normal)
        at_parent_normal = of.to_parent_direction(-at.normal)
        if not my_parent_normal.parallel_to(at_parent_normal):
            print("Vector angle: %f" % my_parent_normal.angle(at_parent_normal), file=sys.stderr)
            raise AssertionError("Normal vectors failed to align!")

        parent_tangent = self.to_parent_direction(my.tangent)
        at_parent_tangent = of.to_parent_direction(at.tangent)
        if not parent_tangent.parallel_to(at_parent_tangent):
            print("Vector angle: %f" % parent_tangent.angle(at_parent_tangent), file=sys.stderr)
            raise AssertionError("Tangent vectors failed to align!")

        # Finally, translate so that `my` lands at `at`
        my_pos = self.to_parent_frame(my.pos)
        at_pos = of.to_parent_frame(at.pos)
        translation = at_pos - my_pos
        self.translate(translation)
