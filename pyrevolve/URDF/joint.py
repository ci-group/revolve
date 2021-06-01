import uuid
import xml.etree.ElementTree

from pyrevolve import URDF
from math import pi


class Joint(URDF.Posable):
    def __init__(self,
                 _id: str,
                 name: str,
                 parent_link: URDF.Link,
                 child_link: URDF.Link,
                 axis: URDF.math.Vector3,
                 coordinates=None,
                 motorized=False,
                 position=None,
                 rotation=None
                 ):
        super().__init__(
            'joint',
            {
                # 'id': _id,
                'name': name,
                'type': 'revolute'
            },
            position=position,
            rotation=rotation,
        )
        self._id = _id
        self._name = name
        self._motorized = motorized
        self._coordinates = coordinates

        xml.etree.ElementTree.SubElement(self, 'parent', {'link': parent_link.name})
        xml.etree.ElementTree.SubElement(self, 'child', {'link': child_link.name})
        self.axis = JointAxis(axis)
        self.append(self.axis)

    def is_motorized(self):
        return self._motorized

    def to_robot_config_sdf(self):
        assert (self.is_motorized())

        servomotor = xml.etree.ElementTree.Element('rv:servomotor', {
            'type': 'position',
            # 'type': 'velocity',
            'id': "{}__rotate".format(self._id),
            'part_id': self._id,
            'part_name': self._name,
            # 'x': self.x,
            # 'y': self.y,
            'joint': self._name,
            # noise: 0.1,
        })

        if self._coordinates is not None:
            servomotor.attrib['coordinates'] = ';'.join(str(i) for i in self._coordinates)

        pid = xml.etree.ElementTree.SubElement(servomotor, 'rv:pid')
        URDF.sub_element_text(pid, 'rv:p', 1.0)
        URDF.sub_element_text(pid, 'rv:i', 0.0)
        URDF.sub_element_text(pid, 'rv:d', 0.0)
        URDF.sub_element_text(pid, 'rv:i_max', 0.0)
        URDF.sub_element_text(pid, 'rv:i_min', 0.0)
        # URDF.sub_element_text(pid, 'rv:cmd_max', 0.0)
        # URDF.sub_element_text(pid, 'rv:cmd_min', 0.0)

        return servomotor


class JointAxis(xml.etree.ElementTree.Element):
    def __init__(self, axis: URDF.math.Vector3):
        xml.etree.ElementTree.SubElement(self, 'axis', {'xyz': '{:e} {:e} {:e}'.format(axis[0], axis[1], axis[2])})
        URDF.sub_element_text(self, 'use_parent_model_frame', '0')

        # TODO calibrate this (load from configuration?)
        xml.etree.ElementTree.SubElement(self, 'limit', {'lower': str(-pi/2),
                                                         'upper': str(pi/2),
                                                         'effort': str(9.4 * 9.8e-02),
                                                         'velocity': str(5.235988e-00)})

    def set_xyz(self, xyz: URDF.math.Vector3):
        self.xyz.text = '{:e} {:e} {:e}'.format(xyz[0], xyz[1], xyz[2])
