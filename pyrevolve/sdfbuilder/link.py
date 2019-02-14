from __future__ import print_function

import sys
import numpy as np

from .physics.inertial import transform_inertia_tensor
from .math import Vector3
from .posable import Posable
from .element import Element
from .physics import Inertial
from .structure import Collision, Visual
from .structure.geometries import Box
from .structure.geometries import Cylinder
from .structure.geometries import Sphere


class Link(Posable):
    """
    Represents a link object
    """
    TAG_NAME = 'link'

    def __init__(self, name, **kwargs):
        """

        :param name:
        :param kwargs:
        :return:
        """
        super(Link, self).__init__(name=name, **kwargs)

        # Only create inertial if required
        self.inertial = kwargs.get("inertial", None)

        self.self_collide = kwargs.get("self_collide", None)

    def render_elements(self):
        """
        :return:
        """
        elements = super(Link, self).render_elements()

        if self.inertial is not None:
            elements.append(self.inertial)

        if self.self_collide is not None:
            elements.append(Element(
                    tag_name="self_collide",
                    body=str(self.self_collide)))

        return elements

    def ensure_inertial(self):
        """
        Creates an inertial element if this
        link does not have one.
        :return:
        """
        if self.inertial is None:
            self.inertial = Inertial()

    def make_color_script(self, color):
        """
        Applies `add_color_script` with the given color to all visuals in this link.
        :param color:
        :type color: str
        :return:
        """
        for visual in self.get_elements_of_type(Visual):
            visual.add_color_script(color)

    def make_color(self, r, g, b, a):
        """
        Applies `add_color` with the given values to all visuals in this link.
        :param r:
        :param g:
        :param b:
        :param a:
        :return:
        """
        for visual in self.get_elements_of_type(Visual):
            visual.add_color(r, g, b, a)

    def make_box(
            self,
            mass,
            x,
            y,
            z,
            collision=True,
            visual=True,
            inertia=True,
            name_prefix=""):
        """
        Shortcut method to `make_geometry` with a box.

        :param mass:
        :param x:
        :param y:
        :param z:
        :param collision: Add a box collision
        :param visual: Add a box visual
        :param inertia: Set box inertia
        :param name_prefix:
        :return: Newly created visual and collision elements, if applicable
        """
        return self.make_geometry(
                geometry=Box(x, y, z, mass),
                collision=collision,
                visual=visual,
                inertia=inertia,
                name_prefix=name_prefix)

    def make_cylinder(
            self,
            mass,
            radius,
            length,
            collision=True,
            visual=True,
            inertia=True,
            name_prefix="",
            tube=False,
            r1=None):
        """
        Shortcut method to `make_geometry` with a cylinder.
        :param mass:
        :param radius:
        :param length:
        :param collision:
        :param visual:
        :param inertia:
        :param name_prefix:
        :param tube: Whether the cylinder should have a tube inertial
        :param r1: If `tube` is `True`, inner radius of the tube
        :return:
        """
        return self.make_geometry(
                geometry=Cylinder(radius, length, mass=mass, tube=tube, r1=r1),
                collision=collision,
                visual=visual,
                inertia=inertia,
                name_prefix=name_prefix)

    def make_sphere(
            self,
            mass,
            radius,
            collision=True,
            visual=True,
            inertia=True,
            name_prefix="",
            solid=True):
        """
        Shortcut method to `make_geometry` with a cylinder.
        :param mass:
        :param radius:
        :param collision:
        :param visual:
        :param inertia:
        :param name_prefix:
        :param solid: Whether the sphere is solid
        :return:
        """
        return self.make_geometry(
                geometry=Sphere(radius, mass=mass, solid=solid),
                collision=collision,
                visual=visual,
                inertia=inertia,
                name_prefix=name_prefix)

    def calculate_inertial(self):
        """
        Calculates and sets this Link's inertial properties by
        iterating all collision elements inside of it and combining
        their Geometry's inertias.

        Note that in order for an inertia tensor to make sense in Gazebo,
        the center of mass needs to be aligned with the `Link` center of mass.
        This method prints an error if this is currently not the case.
        :return:
        """
        if not np.allclose(self.get_center_of_mass().norm(), 0):
            print("WARNING: calculating inertial for link with nonzero center of mass.", file=sys.stderr)

        collisions = self.get_elements_of_type(Collision, recursive=True)
        i_final = np.zeros((3, 3))
        total_mass = 0.0
        for col in collisions:
            rotation = col.get_rotation()
            position = col.get_position()
            geometry = col.geometry
            mass = geometry.get_mass()
            total_mass += mass
            i_final += transform_inertia_tensor(
                mass,
                geometry.get_inertial().get_matrix(),
                position,
                rotation
            )

        self.inertial = Inertial.from_mass_matrix(total_mass, i_final)

    def get_center_of_mass(self):
        """
        Calculate the center of mass of all the collisions inside
        this link.
        :return: The center of mass as determined by all the collision geometries
        :rtype: Vector3
        """
        collisions = self.get_elements_of_type(Collision, recursive=True)
        com = Vector3(0, 0, 0)
        total_mass = 0.0
        for col in collisions:
            geometry = col.geometry
            col_com = col.to_parent_frame(geometry.get_center_of_mass())
            mass = geometry.get_mass()
            com += mass * col_com
            total_mass += mass

        if total_mass > 0:
            com /= total_mass

        return com

    def align_center_of_mass(
            self,
            types=(Posable,),
            recursive=False,
            elements=None):
        """
        Aligns all elements within this link to get the center of mass
        to be at the link's origin. By default, all first level `Posable`
        elements are moved, but this can be changed depending on what is needed.

        :param types: Element types to search for and translate,
                      first argument to `get_elements_of_type`. Defaults to
                      any posable.
        :type types: class-or-tuple
        :param recursive: Second argument to `get_elements_of_type`. Defaults to false.
        :type recursive: bool
        :param elements: Direct iterable of elements to apply transformation to if standard
                         `get_elements_of_type` does not apply.
        :type elements: iterable
        :return:
        :rtype: The translation used on all elements
        """
        translation = -self.get_center_of_mass()
        elms = self.get_elements_of_type(types, recursive=recursive) if elements is None else elements
        for el in elms:
            el.translate(translation)

        return translation

    def make_geometry(
            self,
            geometry,
            collision=True,
            visual=True,
            inertia=True,
            name_prefix=""):
        """
        Gives a link a certain geometry by creating visual and collision objects
        as desired. This should only be called once for a Link, unless
        created items are cleaned up. If `inertia` is set to `True`, the link
        will instantiate its inertia tensor to that of the geometry. Note that
        the geometry must be fully initialized for this to work, as the inertia
        tensor is not updated if the geometry is changed later.

        :param geometry:
        :type geometry: Geometry|CompoundGeometry
        :param collision: Add a box collision
        :type collision: bool
        :param visual: Add a box visual
        :type visual: bool
        :param inertia: Set box inertia
        :type inertia: bool
        :param name_prefix: Prefix for element names (before "visual" / "collision")
        :type name_prefix: str
        :return: List of all created items
        """
        return_value = []

        if inertia:
            # We're given the inertia tensor as it is relative to the geometry's
            # center of mass, and we need it relative to the origin.
            rotation = geometry.get_rotation().conjugated()
            displacement = -geometry.to_parent_frame(geometry.get_center_of_mass())
            self.inertial = geometry.get_inertial().transformed(displacement, rotation)

        if collision:
            col = Collision(name=name_prefix+"collision", geometry=geometry)
            return_value.append(col)
            self.add_element(col)

        if visual:
            vis = Visual(name=name_prefix+"visual", geometry=geometry)
            return_value.append(vis)
            self.add_element(vis)

        return return_value
