import xml.etree.ElementTree
from pyrevolve import SDF


class MeshGeometry(xml.etree.ElementTree.Element):
    def __init__(self, mesh_uri):
        super().__init__('geometry')
        mesh = xml.etree.ElementTree.SubElement(self, 'mesh')
        SDF.sub_element_text(mesh, 'uri', mesh_uri)


class BoxGeometry(xml.etree.ElementTree.Element):
    """
    Box Geometry. This object is not posable, you have to pose the super-object.
    """
    def __init__(self, box_size):
        """
        :param box_size: list or tuple of 3 elements with the 3 sizes (x,y,z).
        """
        super().__init__('geometry')
        self._box = (box_size[0], box_size[1], box_size[2])
        mesh = xml.etree.ElementTree.SubElement(self, 'box')
        SDF.sub_element_text(mesh, 'size',
                             '{:e} {:e} {:e}'.format(box_size[0], box_size[1], box_size[2]))

    @property
    def box(self):
        return self._box


class Material(xml.etree.ElementTree.Element):
    def __init__(self,
                 ambient=(0, 0, 0, 1),
                 diffuse=(0, 0, 0, 1),
                 specular=(0, 0, 0, 1)):
        super().__init__('material')
        SDF.sub_element_text(self, 'ambient',
                             '{} {} {} {}'.format(ambient[0], ambient[1], ambient[2], ambient[3]))
        SDF.sub_element_text(self, 'diffuse',
                             '{} {} {} {}'.format(diffuse[0], diffuse[1], diffuse[2], diffuse[3]))
        SDF.sub_element_text(self, 'specular',
                             '{} {} {} {}'.format(specular[0], specular[1], specular[2], specular[3]))


class Visual(SDF.Posable):
    def __init__(self, name, rgb=(0.94, 0.98, 0.05), position=None, rotation=None):
        super().__init__('visual', {
            'name': '{}_visual'.format(name)
        }, position, rotation)
        material = Material(
            ambient=(rgb[0], rgb[1], rgb[2], 1.0),
            diffuse=(rgb[0], rgb[1], rgb[2], 1.0),
            specular=(0.1, 0.1, 0.1, 1.0),
        )
        self.append(material)


class SurfaceProperties(xml.etree.ElementTree.Element):
    def __init__(self):
        super().__init__('surface')
        contact_tag = xml.etree.ElementTree.SubElement(self, 'contact')
        friction_tag = xml.etree.ElementTree.SubElement(self, 'friction')

        contact_ode_tag = xml.etree.ElementTree.SubElement(contact_tag, 'ode')
        SDF.sub_element_text(contact_ode_tag, 'kd', 10000000.0 / 3)
        SDF.sub_element_text(contact_ode_tag, 'kp', 90000)

        friction_ode_tag = xml.etree.ElementTree.SubElement(friction_tag, 'ode')
        SDF.sub_element_text(friction_ode_tag, 'mu', 1.0)
        SDF.sub_element_text(friction_ode_tag, 'mu2', 1.0)
        SDF.sub_element_text(friction_ode_tag, 'slip1', 0.01)
        SDF.sub_element_text(friction_ode_tag, 'slip2', 0.01)

        friction_bullet_tag = xml.etree.ElementTree.SubElement(friction_tag, 'bullet')
        SDF.sub_element_text(friction_bullet_tag, 'friction', 1.0)
        SDF.sub_element_text(friction_bullet_tag, 'friction2', 1.0)


class Collision(SDF.Posable):
    def __init__(self, name: str, mass: float, position=None, rotation=None):
        """
        :param name: Name of the collision element
        :param mass: Mass of the collision element
        :param position: position of the collision
        :param rotation: rotation of the collision
        """
        self.name = '{}_collision'.format(name)
        super().__init__(
            tag='collision',
            attrib={'name': self.name},
            position=position,
            rotation=rotation
        )

        self.mass = mass
        self._box_geometry = None

        surface_properties = SurfaceProperties()
        self.append(surface_properties)

    def append(self, module):
        super().append(module)
        if type(module) is BoxGeometry:
            if self._box_geometry is not None:
                raise RuntimeError("Adding to many boxes to this collision, only one supported")
            self._box_geometry = module.box

    @property
    def boundaries(self):
        if self._box_geometry is None:
            raise RuntimeError("This Collision element has no BoxGeometry set")
        return (
            (self._box_geometry[0] / -2.0, self._box_geometry[0] / 2.0),  # X
            (self._box_geometry[1] / -2.0, self._box_geometry[1] / 2.0),  # Y
            (self._box_geometry[2] / -2.0, self._box_geometry[2] / 2.0),  # Z
        )

    def get_inertial(self):
        """
        Return solid box inertial
        """
        r = self.mass / 12.0
        x, y, z = self._box_geometry
        ixx = r * (y ** 2 + z ** 2)
        iyy = r * (x ** 2 + z ** 2)
        izz = r * (x ** 2 + y ** 2)
        return SDF.Inertial(mass=self.mass, inertia_xx=ixx, inertia_yy=iyy, inertia_zz=izz)

    def get_center_of_mass(self):
        return self.get_position()
