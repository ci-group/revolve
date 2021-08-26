import xml.dom.minidom
from typing import AnyStr, Optional, List, Iterable

import numpy as np
from isaacgym import gymapi

from pyrevolve.revolve_bot.brain.controller import Actuator, Sensor
from pyrevolve.SDF.math import Vector3


def get_xml_text(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)


class ISAACSensor(Sensor):
    id: AnyStr
    link: AnyStr
    part_id: AnyStr
    name: AnyStr
    type: AnyStr

    def __init__(self, element: xml.dom.minidom.Element):
        super().__init__(1)
        self.id = element.getAttribute("id")
        self.link = element.getAttribute("link")
        self.part_id = element.getAttribute("part_id")
        self.name = element.getAttribute("sensor")
        self.type = element.getAttribute("type")

    def read(self, input: float):
        # TODO this does not work
        input = 0.0


class ISAACActuator(Actuator):
    id: AnyStr
    joint: AnyStr
    part_id: AnyStr
    name: AnyStr
    type: AnyStr
    coordinates: List[float]
    output: float

    def __init__(self, element: xml.dom.minidom.Element):
        self.coordinates = [float(f) for f in element.getAttribute("coordinates").split(';')]
        super().__init__(1, self.coordinates[0], self.coordinates[1], self.coordinates[2])
        self.id = element.getAttribute("id")
        self.joint = element.getAttribute("joint")
        self.part_id = element.getAttribute("part_id")
        self.name = element.getAttribute("part_name")
        self.type = element.getAttribute("type")
        self.output = 0

    def write(self, output: float, step: float):
        self.output = output


class ISAACBot:
    urdf: xml.dom.minidom.Document
    name: AnyStr
    pose: gymapi.Transform
    sensors: List[ISAACSensor]
    actuators: List[ISAACActuator]
    n_weights: int

    def __init__(self, urdf: AnyStr, ground_offset: float = 0.04):
        self.urdf = xml.dom.minidom.parseString(urdf)
        self.pose = gymapi.Transform()

        # Search for robot model (name and pose)
        model_urdf = self.urdf.documentElement
        assert model_urdf.tagName == 'robot'
        self.name = model_urdf.getAttribute('name')

        # Search for robot model pose
        for child in model_urdf.childNodes:
            if child.nodeType != child.TEXT_NODE and child.tagName == 'origin':
                xyz_txt = child.getAttribute('xyz')
                rpy_txt = child.getAttribute('rpy')
                xyz = [float(f) for f in xyz_txt.split(' ')]
                rpy = [float(f) for f in rpy_txt.split(' ')]
                # Convert from gazebo system
                # TODO verify this is correct
                # x->x
                # y->z
                # z->-y
                self.pose.p = gymapi.Vec3(
                    xyz[0],
                    xyz[1],
                    xyz[2] + ground_offset,
                )
                # TODO verify this is correct
                self.pose.r = gymapi.Quat.from_euler_zyx(
                    rpy[0],
                    rpy[1],
                    rpy[2],
                )
                break
        else:
            self.pose.p = gymapi.Vec3(0, 0, ground_offset)
            self.pose.r = gymapi.Quat(0.0, 0.0, 0.0, 0.707107)

        self.sensors = [s for s in self._list_sensors()]
        self.actuators = [a for a in self._list_actuator()]

        self.n_weights, self.connection_list = self._compute_n_weights()
        self.actuator_map = np.arange(self.n_weights)

    def joints(self) -> Iterable[xml.dom.minidom.Element]:
        for joint in self.urdf.documentElement.getElementsByTagName('joint'):
            yield joint

    def links(self) -> Iterable[xml.dom.minidom.Element]:
        for link in self.urdf.documentElement.getElementsByTagName('link'):
            yield link

    def _list_sensors(self) -> Iterable[ISAACSensor]:
        sensors_xml = self.urdf.documentElement.getElementsByTagName('rv:sensors')[0]
        for sensor in sensors_xml.getElementsByTagName('rv:sensor'):
            yield ISAACSensor(sensor)

    def _list_actuator(self) -> Iterable[ISAACActuator]:
        actuators_xml = self.urdf.documentElement.getElementsByTagName('rv:actuators')[0]
        for actuator in actuators_xml.childNodes:
            if actuator.nodeType != actuator.TEXT_NODE:
                yield ISAACActuator(actuator)

    def _compute_n_weights(self) -> (int, list):
        n_intra_connections = len(self.actuators)
        n_extra_connections = 0

        connection_list = []
        element = 0
        for act_a in self.actuators:
            row = element // n_intra_connections
            for act_b in self.actuators:
                col = element % n_intra_connections
                element += 1
                if col <= row:  # only consider upper-triangular connections
                    continue

                # TODO define better method than manhattan distance
                import math
                coord_a = Vector3(act_a.coordinates)
                coord_b = Vector3(act_b.coordinates)
                dist_x = math.fabs(coord_a.x - coord_b.x)
                dist_y = math.fabs(coord_a.y - coord_b.y)
                dist_z = math.fabs(coord_a.z - coord_b.z)
                man_dist = dist_x + dist_y + dist_z
                if 0.01 < man_dist < 2.01:
                    n_extra_connections += 1
                    connection_list.append((row, col))  # remember pos list of intra-neuron connections
        return n_intra_connections + n_extra_connections, connection_list

    def create_actuator_map(self, actuator_dict: dict):
        index = list(actuator_dict.values())
        keys = list(actuator_dict.keys())
        self.actuator_map = [index[keys.index(act.joint)] for act in self.actuators]

    def create_CPG_network(self, weights) -> np.array:
        assert (len(weights) == self.n_weights)
        n_dof = len(self.actuators)
        intra_connections = np.diag(weights[:n_dof], 0)
        inter_connections = np.zeros_like(intra_connections)
        for ind, index in enumerate(self.connection_list):
            inter_connections[index] = weights[n_dof + ind]
        weight_matrix = np.zeros((n_dof * 2, n_dof * 2))
        weight_matrix[0::2, 1::2] = intra_connections  # place connection within oscillators x -> y
        weight_matrix[0::2, 0::2] += inter_connections  # place connections between oscillators x -> x
        weight_matrix -= weight_matrix.T  # copy weights in anti-symmetric direction
        return weight_matrix

    def learner(self) -> xml.dom.minidom.Element:
        return self.urdf.documentElement.getElementsByTagName('rv:learner')[0]

    def controller(self) -> xml.dom.minidom.Element:
        return self.urdf.documentElement.getElementsByTagName('rv:controller')[0]
