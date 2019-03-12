import xml.etree.ElementTree
from pyrevolve import SDF
from pyrevolve.sdfbuilder import math as SDFmath


class Joint(SDF.Posable):
    def __init__(self, name: str, parent_link: SDF.Link, child_link: SDF.Link, axis: SDFmath.Vector3, position=None,
                 rotation=None):
        super().__init__(
            'joint',
            {'name': name, 'type': 'revolute'},
            position=position,
            rotation=rotation,
        )
        SDF.sub_element_text(self, 'parent', parent_link.name)
        SDF.sub_element_text(self, 'child', child_link.name)
        self.axis = JointAxis(axis)
        self.append(self.axis)


class JointAxis(xml.etree.ElementTree.Element):
    def __init__(self, axis: SDFmath.Vector3):
        super().__init__('axis')
        self.xyz = SDF.sub_element_text(self, 'xyz',
                                        '{:e} {:e} {:e}'.format(axis[0], axis[1], axis[2]))
        SDF.sub_element_text(self, 'use_parent_model_frame', '0')
        limit = xml.etree.ElementTree.SubElement(self, 'limit')

        # TODO calibrate this (load from configuration?)
        SDF.sub_element_text(limit, 'lower', -7.853982e-01)
        SDF.sub_element_text(limit, 'upper', 7.853982e-01)
        SDF.sub_element_text(limit, 'effort', 1.765800e-01)
        SDF.sub_element_text(limit, 'velocity', 5.235988e+00)

    def set_xyz(self, xyz: SDFmath.Vector3):
        self.xyz.text = '{:e} {:e} {:e}'.format(xyz[0], xyz[1], xyz[2])
