import uuid
import xml.etree.ElementTree
from pyrevolve import SDF
import pyrevolve.SDF.math


class Joint(SDF.Posable):
    def __init__(self,
                 _id: str,
                 name: str,
                 parent_link: SDF.Link,
                 child_link: SDF.Link,
                 axis: SDF.math.Vector3,
                 lower_limit: float,
                 upper_limit: float,
                 effort_limit: float,
                 velocity_limit: float,
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

        SDF.sub_element_text(self, 'parent', parent_link.name)
        SDF.sub_element_text(self, 'child', child_link.name)
        self.axis = JointAxis(axis,
                              lower_limit,
                              upper_limit,
                              effort_limit,
                              velocity_limit,
        )
        self.append(self.axis)

    def is_motorized(self):
        return self._motorized

    def to_robot_config_sdf(self):
        assert (self.is_motorized())

        servomotor = xml.etree.ElementTree.Element('rv:servomotor', {
            'type': 'position',
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
        SDF.sub_element_text(pid, 'rv:p', 1.0)
        SDF.sub_element_text(pid, 'rv:i', 0.0)
        SDF.sub_element_text(pid, 'rv:d', 0.0)
        SDF.sub_element_text(pid, 'rv:i_max', 0.0)
        SDF.sub_element_text(pid, 'rv:i_min', 0.0)
        # SDF.sub_element_text(pid, 'rv:cmd_max', 0.0)
        # SDF.sub_element_text(pid, 'rv:cmd_min', 0.0)

        return servomotor


class JointAxis(xml.etree.ElementTree.Element):
    def __init__(self,
                 axis: SDF.math.Vector3,
                 lower_limit: float,
                 upper_limit: float,
                 effort_limit: float,
                 velocity_limit: float):
        super().__init__('axis')
        self.xyz = SDF.sub_element_text(self, 'xyz',
                                        '{:e} {:e} {:e}'.format(axis[0], axis[1], axis[2]))
        SDF.sub_element_text(self, 'use_parent_model_frame', '0')
        limit = xml.etree.ElementTree.SubElement(self, 'limit')

        # TODO calibrate this (load from configuration?)
        SDF.sub_element_text(limit, 'lower', lower_limit)
        SDF.sub_element_text(limit, 'upper', upper_limit)
        SDF.sub_element_text(limit, 'effort', effort_limit)
        SDF.sub_element_text(limit, 'velocity', velocity_limit)

    def set_xyz(self, xyz: SDF.math.Vector3):
        self.xyz.text = '{:e} {:e} {:e}'.format(xyz[0], xyz[1], xyz[2])
