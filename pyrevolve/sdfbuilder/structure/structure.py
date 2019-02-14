"""
Collision / visual and geometry like classes
"""
from ..posable import Posable
from ..posable import PosableGroup
from ..element import Element
from .geometries import CompoundGeometry


class Structure(Posable):
    """
    Base class for collision/visual elements
    """
    def __init__(self, name, geometry, **kwargs):
        """

        :param name:
        :param geometry:
        :type geometry: CompoundGeometry|Geometry
        :param kwargs:
        :return:
        """
        super(Structure, self).__init__(name, **kwargs)

        # Only the geometry of a structure has a pose
        self._pose = None
        self.geometry = geometry

    # Delegate all position and rotation calls to the geometry object
    def set_position(self, position):
        self.geometry.set_position(position)

    def set_rotation(self, rotation):
        self.geometry.set_rotation(rotation)

    def get_position(self):
        return self.geometry.get_position()

    def get_rotation(self):
        return self.geometry.get_rotation()

    def get_pose(self):
        return self.geometry.get_pose()

    def render_elements(self):
        """
        :return:
        """
        return super(Structure, self).render_elements() + [self.geometry]

    def render(self):
        """
        Override render to create a list of sub elements instead of a
        parent element if the child is a compound.
        :return:
        """
        if not isinstance(self.geometry, CompoundGeometry):
            return super(Structure, self).render()

        geometries = self.geometry.geometries

        elements = []
        for i in range(len(geometries)):
            # Create a new element of self-type that inherits
            # all this structure's properties.
            # Note that if one of these geometries is again a compound
            # geometry, its render method will do the same thing as this
            # and produce a list of objects.
            elements.append(self.__class__(
                name=self.name+"_"+str(i),
                geometry=geometries[i],
                elements=self.elements,
                body=self.body,
                attributes=self.attributes
            ))

        return "".join(str(el) for el in elements)


class Collision(Structure):
    TAG_NAME = 'collision'


class Visual(Structure):
    TAG_NAME = 'visual'

    def add_color_script(self, color):
        """
        Adds a new Material element to this Visual that has a color
        script for the given color.
        :param color: One of Gazebo's supported colors, see
        `https://bitbucket.org/osrf/gazebo/src/52abccccfec20a5f96da9dc0aeda830b48a66269/media/materials/scripts/gazebo.material?at=default`
        :return:
        """
        if color.index('/') < 0:
            color = "Gazebo/"+color.title()

        self.add_element(Material(
                body="\n"
                     "<script>\n"
                     "  <name>{}</name>\n"
                     "</script>".format(color)))

    def add_color(self, r, g, b, a=1):
        """
        Simple color setter that adds a `Material` element with the
        ambient / diffuse values at the given r,g,b,a values and
        specular set to (0.1, 0.1, 0.1, a).
        :return:
        """
        color = '{r} {g} {b} {a}'.format(r=r, g=g, b=b, a=a)
        specular = '0.1 0.1 0.1 {}'.format(a)
        self.add_element(Material(
                body="\n"
                     "  <ambient>{ambient}</ambient>\n"
                     "  <diffuse>{diffuse}</diffuse>\n"
                     "  <specular>{specular}</specular>\n".format(
                        ambient=color,
                        diffuse=color,
                        specular=specular)))


class StructureCombination(PosableGroup):
    """
    PosableGroup wrapper over a visual and a collision element
    that share a Geometry.
    """

    def __init__(self, name, geometry, **kwargs):
        """
        :param name:
        :type name: str
        :param geometry:
        :type geometry: Geometry
        :param kwargs:
        :return:
        """
        super(StructureCombination, self).__init__(name, **kwargs)
        self.geometry = geometry
        self.collision = Collision(name+"_collision", geometry.copy())
        self.visual = Visual(name+"_visual", geometry.copy())
        self.add_elements([self.collision, self.visual])


class Material(Element):
    TAG_NAME = 'material'
