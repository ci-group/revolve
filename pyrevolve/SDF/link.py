import xml.etree.ElementTree
from pyrevolve import SDF


class Link(SDF.Posable):
    def __init__(self, name, self_collide=True, position=None, rotation=None):
        super().__init__(
            'link',
            {'name': name},
            position,
            rotation,
        )

        SDF.sub_element_text(self, 'self_collide', self_collide)


class BoxLink(Link):
    def __init__(self, name, self_collide=True, position=None, rotation=None):
        super().__init__(
            'link_component_{}__box'.format(name),
            self_collide,
            position,
            rotation,
        )

        self.size = (0, 0, 0, 0, 0, 0)

    def append(self, subelement):
        if type(subelement) is SDF.Collision:
            # box = subelement.
            pass

        super().append(subelement)

    def align_center_of_mass(self):
        raise NotImplementedError("TODO")

    def calculate_inertial(self):
        raise NotImplementedError("TODO")


class Inertial(xml.etree.ElementTree.Element):
    def __init__(self, mass, inertia_xx, inertia_xy, inertia_xz, inertia_yy, inertia_yz, inertia_zz):
        super().__init__('inertial')

        SDF.sub_element_text(self, 'mass', mass)

        inertia = xml.etree.ElementTree.SubElement(self, 'inertia')
        SDF.sub_element_text(inertia, 'ixx', inertia_xx)
        SDF.sub_element_text(inertia, 'ixy', inertia_xy)
        SDF.sub_element_text(inertia, 'ixz', inertia_xz)
        SDF.sub_element_text(inertia, 'iyy', inertia_yy)
        SDF.sub_element_text(inertia, 'iyz', inertia_yz)
        SDF.sub_element_text(inertia, 'izz', inertia_zz)
