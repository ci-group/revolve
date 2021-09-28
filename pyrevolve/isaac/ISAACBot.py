import math
import random
import xml.dom.minidom
from typing import AnyStr, List, Iterable, Callable, Optional

import numpy as np
import sqlalchemy.orm
from isaacgym import gymapi

from pyrevolve.SDF.math import Vector3
from pyrevolve.revolve_bot.brain.controller import Actuator, Sensor
from pyrevolve.revolve_bot.brain.controller import Controller as RevolveController
from pyrevolve.revolve_bot.brain.controller import DifferentialCPG, DifferentialCPG_ControllerParams
from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase
from pyrevolve.util.supervisor.rabbits import Robot as DBRobot
from pyrevolve.util.supervisor.rabbits import RobotEvaluation as DBRobotEvaluation
from pyrevolve.util.supervisor.rabbits import RobotState as DBRobotState


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
    # Controller stuff
    controller: RevolveController
    sensors: List[ISAACSensor]
    actuators: List[ISAACActuator]
    n_weights: int
    # Sym stuff
    handle: int
    env_index: int
    pose: gymapi.Transform
    born_time: Optional[float]
    life_duration: float
    # Database Stuff
    db_robot: DBRobot
    evals: List[DBRobotEvaluation]

    def __init__(self, urdf: AnyStr, ground_offset: float = 0.04, life_duration: float = math.inf):
        self.urdf = xml.dom.minidom.parseString(urdf)
        self.pose = gymapi.Transform()
        self.life_duration = life_duration

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

        # Database stuff
        self.db_robot = None
        self.evals = []

        # Controller Stuff
        self.sensors = [s for s in self._list_sensors()]
        self.actuators = [a for a in self._list_actuator()]

        self.n_weights, self.connection_list = self._compute_n_weights()
        self.actuator_map = np.arange(self.n_weights)

        self.controller = self._create_controller()

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

    def _create_controller(self) -> RevolveController:
        controller_type: AnyStr = self.controller_desc().getAttribute('type')
        learner_type: AnyStr = self.learner_desc().getAttribute('type')
        controller: RevolveController

        if controller_type == 'cpg-python':
            params: DifferentialCPG_ControllerParams = self._extract_cpg_urdf_params()
            if not params.weights:
                params.weights = [random.uniform(0, 1) for _ in range(self.n_weights)]
            matrix = self._create_python_cpg_network(params.weights)
            # TODO use the python controller!
            controller = DifferentialCPG(params, self.actuators)
        elif controller_type == 'cpg':
            params: DifferentialCPG_ControllerParams = self._extract_cpg_urdf_params()
            if not params.weights:
                params.weights = [random.uniform(0, 1) for _ in range(self.n_weights)]
            params.weights = [random.uniform(0, 1) for _ in range(self.n_weights)]
            controller = DifferentialCPG(params, self.actuators)
        elif controller_type == 'cppn-cpg':
            params: DifferentialCPG_ControllerParams = self._extract_cpg_urdf_params()
            # TODO load cppn-network from URDF element and use that to generate weights
            if not params.weights:
                params.weights = [random.uniform(0, 1) for _ in range(self.n_weights)]
            params.weights = [random.uniform(0, 1) for _ in range(self.n_weights)]
            controller = DifferentialCPG(params, self.actuators)
        else:
            raise RuntimeError(f'unsupported controller "{controller_type}"')

        return controller

    def _extract_cpg_urdf_params(self) -> DifferentialCPG_ControllerParams:
        controller_urdf: xml.dom.minidom.Element = self.controller_desc()
        params = DifferentialCPG_ControllerParams()
        controller_type: AnyStr = controller_urdf.getAttribute('type')
        for key, value in controller_urdf.attributes.items():
            if not hasattr(params, key):
                print(f"{controller_type}-controller has no parameter: {key}")
                continue
            try:
                if key == 'weights':
                    value = f"[{value.replace(';', ',')}]"
                setattr(params, key, eval(value))
            except:
                print(f"URDF parameter {key} has invalid value {value} -> requires type: {type(params.__getattribute__(key))}")
            return params

    def _create_python_cpg_network(self, weights) -> np.array:
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

    def learner_desc(self) -> xml.dom.minidom.Element:
        return self.urdf.documentElement.getElementsByTagName('rv:learner')[0]

    def controller_desc(self) -> xml.dom.minidom.Element:
        return self.urdf.documentElement.getElementsByTagName('rv:controller')[0]

    def update_robot(self,
                     time: float,
                     delta: float,
                     gym,
                     robot_states_session: sqlalchemy.orm.session) -> None:
        """
        Updates the robot (controller, position and database state)
        :param time: simulator wall clock in seconds
        :param delta: delta seconds since the last update_robot
        :param gym: pointer to the gym object
        :param robot_states_session: database session to save the robot state
        """

        self.controller.update(self.actuators, self.sensors, time, delta)
        # TODO order needs to be readjusted here
        position_target = [act.output for act in self.actuators]
        gym.set_robot_dof_position_targets(self.env_index, self.handle, position_target)

        # Database data
        time_nsec, time_sec = math.modf(time)
        time_nsec *= 1_000_000_000

        robot_pose = gym.get_robot_position_rotation(self.env_index, self.handle)
        robot_pos: gymapi.Vec3 = robot_pose[0]
        robot_rot: gymapi.Quat = robot_pose[1]

        # Save current robot state and queue to the database
        db_state = DBRobotState(evaluation=self.evals[-1], time_sec=int(time_sec), time_nsec=int(time_nsec),
                                # We swap x and z to have the data saved the same way as gazebo
                                pos_x=float(robot_pos[0]),
                                pos_y=float(robot_pos[1]),
                                pos_z=float(robot_pos[2]),
                                rot_quaternion_x=float(robot_rot[0]), rot_quaternion_y=float(robot_rot[1]),
                                rot_quaternion_z=float(robot_rot[2]), rot_quaternion_w=float(robot_rot[3]),
                                orientation_left=0, orientation_right=0, orientation_forward=0, orientation_back=0)
        robot_states_session.add(db_state)

    # def _learning_step(self, value_function: Callable[[int, int], float]):
    #     """
    #     Executes Learning code
    #     :param value_function: function that computes the value of the controller,
    #     given environment index and robot handle
    #     """
    #     if not learning_eval_finished:
    #         return
    #     with db.session() as session:
    #         controller_value = value_function(self.env_index, self.handle)
    #         eval = self.evals[-1]
    #         eval.fitness = float(controller_value)
    #         # evals[0].controller = str(
    #         #     _controller.get_weights())
    #         session.add(eval)
    #         session.commit()

    def death_time(self) -> float:
        if self.life_duration is None:
            return math.inf
        born_time: float = self.born_time if self.born_time is not None else 0.0
        return self.born_time + self.life_duration