"""
Simple geometries such as box, cylinder and sphere.
"""
from __future__ import division
from ..math import Vector3
from ..posable import Posable, PosableGroup
from ..util import number_format as nf
from ..physics.inertial import Inertial, transform_inertia_tensor
import numpy as np


class BaseGeometry(object):
    """
    Defines an interface for geometries.
    """

    def get_inertial(self):
        """
        If implemented in the base class, returns an inertial corresponding to
        this simple shape. This inertial can then be used in a link.

        The inertial is relative to the geometry's center of mass.
        :return:
        :rtype: Inertial
        """
        raise NotImplementedError("`get_inertial` is not implemented.")

    def get_center_of_mass(self):
        """
        Return the center of mass for this geometry.

        :return: Center of mass in the local frame.
        :rtype: Vector3
        """
        raise NotImplementedError("`get_center_of_mass` is not implemented.")

    def get_mass(self):
        """
        Return the mass of this geometry.
        :return: Mass
        :rtype: float
        """
        raise NotImplementedError("`get_mass` is not implemented.")


class Geometry(Posable, BaseGeometry):
    """
    Base geometry class. We've made this posable for a convenient use with
    the CompoundGeometry class.
    """
    TAG_NAME = 'geometry'
    RENDER_POSE = False

    def __init__(self, mass=None, pose=None, **kwargs):
        """
        :param pose:
        :param mass: Mass of this geometry. If you're only using it
                     as a visual, you can probably leave this empty.
        :type mass: float
        :return:
        """
        super(Geometry, self).__init__(None, pose, **kwargs)
        self.mass = mass

    def get_mass(self):
        """
        Return the mass of this geometry.
        """
        return self.mass

    def get_center_of_mass(self):
        """
        For most geometries, the center of mass will simply lie at the origin.
        This is therefore returned by default for simple geometries.
        """
        return Vector3(0, 0, 0)


class CompoundGeometry(PosableGroup, BaseGeometry):
    """
    A helper class for combining multiple geometries
    """

    def get_mass(self):
        """
        Returns the total mass of all geometries.
        :return:
        """
        return sum(geometry.get_mass() for geometry in self.geometries)

    def get_center_of_mass(self):
        """
        :return:
        :rtype: Vector3
        """
        total_mass = 0.0
        center_mass = Vector3(0, 0, 0)
        for geometry in self.geometries:
            # Get the geometry's center of mass and translate it to the
            # frame of the posable. Since the `CompoundGeometry` is a
            # `PosableGroup`, this can be achieved by sibling translation.
            geom_center = geometry.to_sibling_frame(
                geometry.get_center_of_mass(),
                self
            )

            mass = geometry.get_mass()
            total_mass += mass
            center_mass += mass * geom_center

        return center_mass / total_mass

    def __init__(self, **kwargs):
        """
        CompoundGeometry constructor
        """
        super(CompoundGeometry, self).__init__(**kwargs)
        self.geometries = []

    def add_geometry(self, geometry):
        """
        Adds a geometry to the group along with all the possible
        arguments required to get its inertia.
        :param geometry:
        :type geometry: Geometry|CompoundGeometry
        """
        self.geometries.append(geometry)

    def get_inertial(self):
        """
        Returns the inertia tensor for all the combined positioned
        geometries in this compound geometry.

        Uses the first part of this question:
        http://physics.stackexchange.com/questions/17336/how-do-you-combine-two-rigid-bodies-into-one
        """
        # Calculate the center of mass
        center_mass = self.get_center_of_mass()

        # The final inertia matrix
        i_final = np.zeros((3, 3))
        for geometry in self.geometries:
            # We need the center of mass again
            geom_center = geometry.to_sibling_frame(
                geometry.get_center_of_mass(),
                self
            )

            # We have the inertia tensor in the object's frame,
            # i.e. as if it isn't rotated. We want to return it
            # in this object's frame, i.e. as if the compound isn't
            # rotated. The rotation for that is the total rotation
            # of the object, with the rotation of the compound cancelled
            # out. Conceptually, we now start with the inertia tensor
            # as if the object has zero rotation, and calculate the tensor
            # resulting from rotating the object around its actual rotation.
            rotation = self.get_rotation().conjugated() * geometry.get_rotation()
            j1 = transform_inertia_tensor(
                geometry.get_mass(),
                geometry.get_inertial().get_matrix(),
                center_mass - geom_center,
                rotation
            )
            i_final += j1

        total_mass = self.get_mass()
        inertial = Inertial.from_mass_matrix(total_mass, i_final)
        return inertial


class Box(Geometry):
    """
    Represents a box geometry, i.e.
    a geometry *with* a box object
    """
    def __init__(self, x, y, z, mass=None, **kwargs):
        """

        :param x:
        :param y:
        :param z:
        :param kwargs:
        :return:
        """
        super(Box, self).__init__(mass=mass, **kwargs)
        self.size = (x, y, z)

    def render_elements(self):
        """
        Add box tag
        :return:
        """
        elements = super(Box, self).render_elements()

        x, y, z = self.size
        elements.append("<box><size>%s %s %s</size></box>" % (nf(x), nf(y), nf(z)))
        return elements

    def get_inertial(self):
        """
        Return solid box inertial
        """
        mass = self.get_mass()
        r = mass / 12.0
        x, y, z = self.size
        ixx = r * (y**2 + z**2)
        iyy = r * (x**2 + z**2)
        izz = r * (x**2 + y**2)
        return Inertial(mass=mass, ixx=ixx, iyy=iyy, izz=izz)


class Cylinder(Geometry):
    """
    Cylinder geometry
    """
    def __init__(self, radius, length, mass=None, tube=False, r1=None, **kwargs):
        """
        Cylinder geometry. The cylinder is defined as being a circle
        with the given radius in x / y directions, whilst having the
        given length in the z direction.

        :param radius: (x and y directions)
        :type radius: float
        :param length: Length (z-direction)
        :type length: float
        :param tube: If true, the inertial properties for this geometry will be those of a tube.
        :type tube: bool
        :param r1: If `tube` is true, the radius of the inner cylinder of the tube
        :param kwargs:
        """
        super(Cylinder, self).__init__(mass=mass, **kwargs)
        self.tube, self.r1 = tube, r1
        self.radius, self.length = radius, length

    def render_elements(self):
        """
        Add box tag
        :return:
        """
        elements = super(Cylinder, self).render_elements()

        elements.append("<cylinder><radius>%s</radius><length>%s</length></cylinder>"
                        % (nf(self.radius), nf(self.length)))
        return elements

    def get_inertial(self):
        """
        Return cylinder inertial. You can specify `tube=True` alongside
        the radius of the center hole to get the inertia of a cylindrical tube.
        """
        if self.tube:
            if self.r1 is None:
                raise AttributeError("Tube inertia requires `r1` radius for cylinder.")

            r = self.radius**2 + self.r1**2
        else:
            r = self.radius**2

        mass = self.get_mass()
        ixx = (3 * r + self.length**2) * mass / 12.0
        izz = 0.5 * mass * r
        return Inertial(mass=mass, ixx=ixx, iyy=ixx, izz=izz)


class Sphere(Geometry):
    """
    Sphere geometry
    """
    def __init__(self, radius, mass=None, solid=True, **kwargs):
        """
        Create a new sphere geometry
        :param radius: (x and y directions)
        :type radius: float
        :param solid: Whether this is a solid or hollow sphere, influences only inertia
        :type solid: bool
        :param kwargs:
        """
        super(Sphere, self).__init__(mass=mass, **kwargs)
        self.solid = solid
        self.radius = radius

    def render_elements(self):
        """
        Add box tag
        :return:
        """
        elements = super(Sphere, self).render_elements()

        elements.append("<sphere><radius>%s</radius></sphere>"
                        % nf(self.radius))
        return elements

    def get_inertial(self):
        """
        Return cylinder inertial
        """
        mass = self.mass
        frac = 5.0 if self.solid else 3.0
        ixx = (2 * mass * self.radius**2) / frac
        return Inertial(mass=mass, ixx=ixx, iyy=ixx, izz=ixx)


class Mesh(Geometry):
    """
    Mesh geometry. Since we cannot determine the inertia
    of meshes here, you need to extend this class with
    the full geometry methods in order to use this for
    anything else than a visual.
    """

    def __init__(self, uri, scale=None, **kwargs):
        super(Mesh, self).__init__(**kwargs)
        self.uri = uri
        self.scale = scale

    def render_elements(self):
        """
        Adds the mesh geometry
        :return:
        """
        elements = super(Mesh, self).render_elements()

        if self.scale is not None:
            try:
                x, y, z = self.scale
            except TypeError:
                x = y = z = self.scale

            scale = "<scale>%s %s %s</scale>" % (nf(x), nf(y), nf(z))
        else:
            scale = ""

        elements.append("<mesh><uri>%s</uri>%s</mesh>" % (self.uri, scale))
        return elements
