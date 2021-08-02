"""
Revolve body generator based on RoboGen framework
"""
from __future__ import annotations

import math
import os
from collections import OrderedDict, deque
from typing import TYPE_CHECKING

import numpy as np
import yaml
from pyrevolve import SDF
from pyrevolve.custom_logging.logger import logger

from .brain import Brain, BrainNN
from .measure.measure_body_3d import MeasureBody3D
from .measure.measure_brain import MeasureBrain
from .render.brain_graph import BrainGraph
from .render.render import Render
from .revolve_module import CoreModule, Orientation, rotate_matrix_x_axis

if TYPE_CHECKING:
    from typing import AnyStr, Dict, Iterable, Optional, Union

    from pyrevolve.tol.manage.measures import BehaviouralMeasurements

    from .revolve_module import RevolveModule


class RevolveBot:
    """
    Basic robot description class that contains robot's body and/or brain
    structures, ID and several other necessary parameters. Capable of reading
    a robot's sdf mode
    """

    def __init__(self, _id: int = None, self_collide: bool = True):
        self._id: int = _id
        self._body: Optional[CoreModule] = None
        self._brain: Optional[Brain] = None
        self._morphological_measurements: Optional[MeasureBody3D] = None
        self._brain_measurements: Optional[MeasureBrain] = None
        self._behavioural_measurements: Optional[BehaviouralMeasurements] = None
        self.self_collide: bool = self_collide
        self.battery_level: float = 0.0
        self.simulation_boundaries = None
        self.failed_eval_attempt_count: int = 0

    @property
    def id(self) -> int:
        return self._id

    @property
    def body(self) -> CoreModule:
        return self._body

    @property
    def brain(self) -> Brain:
        return self._brain

    def size(self) -> int:
        robot_size = 1 + self._recursive_size_measurement(self._body)
        return robot_size

    def _recursive_size_measurement(self, module) -> int:
        count: int = 0
        for _, child in module.iter_children():
            if child is not None:
                count += 1 + self._recursive_size_measurement(child)

        return count

    def measure_behaviour(self):
        """

        :return:
        """
        raise NotImplementedError("Behaviour measurement is not implemented here")

    def measure_phenotype(self) -> None:
        self._morphological_measurements = self.measure_body()
        self._brain_measurements = self.measure_brain()
        logger.info("Robot " + str(self.id) + " was measured.")

    def measure_body(self) -> MeasureBody3D:
        """
        :return: instance of MeasureBody3D after performing all measurements
        """
        if self._body is None:
            raise RuntimeError("Body not initialized")
        try:
            measure = MeasureBody3D(self._body)
            measure.measure_all()
            return measure
        except Exception as e:
            logger.exception("Failed measuring body")

    def export_phenotype_measurements(self, data_path) -> None:
        filepath = os.path.join(
            data_path, "descriptors", f"phenotype_desc_{self.id}.txt"
        )
        with open(filepath, "w+") as file:
            if self._morphological_measurements is not None:
                for (
                    key,
                    value,
                ) in self._morphological_measurements.measurements_to_dict().items():
                    file.write(f"{key} {value}\n")
            if self._brain_measurements is not None:
                for (
                    key,
                    value,
                ) in self._brain_measurements.measurements_to_dict().items():
                    file.write(f"{key} {value}\n")

    def measure_brain(self) -> MeasureBrain:
        """
        :return: instance of MeasureBrain after performing all measurements
        """
        try:
            measure = MeasureBrain(self._brain, 10)
            measure_b = MeasureBody3D(self._body)
            measure_b.count_active_hinges()
            if measure_b.active_hinges_count > 0:
                measure.measure_all()
            else:
                measure.set_all_zero()
            return measure
        except Exception as e:
            logger.error(f"Failed measuring brain: {e}")

    def load(self, text: AnyStr, conf_type: str) -> None:
        """
        Load robot's description from a string and parse it to Python structure
        :param text: Robot's description string
        :param conf_type: Type of a robot's description format
        """
        if "yaml" == conf_type:
            self.load_yaml(text)
        elif "sdf" == conf_type:
            raise NotImplementedError("Loading from SDF not yet implemented")

    def load_yaml(self, text: AnyStr) -> None:
        """
        Load robot's description from a yaml string
        :param text: Robot's yaml description
        """
        yaml_bot = yaml.safe_load(text)
        self._id = yaml_bot["id"] if "id" in yaml_bot else None
        self._body = CoreModule.FromYaml(yaml_bot["body"])

        try:
            if "brain" in yaml_bot:
                yaml_brain = yaml_bot["brain"]
                if "type" not in yaml_brain:
                    # raise IOError("brain type not defined, please fix it")
                    yaml_brain["type"] = "neural-network"
                self._brain = Brain.from_yaml(yaml_brain)
            else:
                self._brain = Brain()
        except:
            self._brain = Brain()
            logger.exception("Failed to load brain, setting to None")

    def load_file(self, path: str, conf_type: str = "yaml") -> None:
        """
        Read robot's description from a file and parse it to Python structure
        :param path: Robot's description file path
        :param conf_type: Type of a robot's description format
        :return:
        """
        with open(path, "r") as robot_file:
            robot = robot_file.read()

        self.load(robot, conf_type)

    def to_sdf(
        self, pose=SDF.math.Vector3(0, 0, 0.25), nice_format: Union[bool, str] = None
    ) -> AnyStr:
        if type(nice_format) is bool:
            nice_format = "\t" if nice_format else None
        return SDF.revolve_bot_to_sdf(
            self, pose, nice_format, self_collide=self.self_collide
        )

    def to_yaml(self) -> AnyStr:
        """
        Converts robot data structure to yaml
        :return:
        """
        yaml_dict = OrderedDict()
        yaml_dict["id"] = self._id
        yaml_dict["body"] = self._body.to_yaml()
        if self._brain is not None:
            yaml_dict["brain"] = self._brain.to_yaml()

        return yaml.dump(yaml_dict)

    def save_file(self, path: str, conf_type: str = "yaml") -> None:
        """
        Save robot's description on a given file path in a specified format
        :param path:
        :param conf_type:
        :return:
        """
        robot: str = ""
        if "yaml" == conf_type:
            robot = self.to_yaml()
        elif "sdf" == conf_type:
            robot = self.to_sdf(nice_format=True)
        else:
            raise NotImplementedError(f"Config type {conf_type} not supported")

        with open(path, "w") as robot_file:
            robot_file.write(robot)

    def update_substrate(self, raise_for_intersections: bool = False) -> None:
        """
        Update all coordinates for body components

        :param raise_for_intersections: enable raising an exception if a collision of coordinates is detected
        :raises self.ItersectionCollisionException: If a collision of coordinates is detected (and check is enabled)
        """
        substrate_coordinates_map: Dict[(int, int, int), int] = {
            (0, 0, 0): self._body.id
        }
        self._body.substrate_coordinates = (0, 0, 0)
        self._update_substrate(
            raise_for_intersections,
            self._body,
            np.identity(3),
            substrate_coordinates_map,
        )

    class ItersectionCollisionException(Exception):
        """
        A collision has been detected when updating the robot coordinates.
        Check self.substrate_coordinates_map to know more.
        """

        def __init__(self, substrate_coordinates_map: Dict[(int, int, int), int]):
            super().__init__(self)
            self.substrate_coordinates_map: Dict[
                (int, int, int), int
            ] = substrate_coordinates_map

    def _update_substrate(
        self,
        raise_for_intersections: bool,
        parent: RevolveModule,
        global_rotation_matrix: np.array,
        substrate_coordinates_map: Dict[(int, int, int), int],
    ):

        step = np.array([[1], [0], [0]])

        # rotation of parent
        # parent.orientation != of type Orientation but is an angle
        # Orientation of coreBlock is null!

        if parent.orientation != None:
            rot = round(parent.orientation)
        else:
            rot = 0
        vertical_rotation_matrix = rotate_matrix_x_axis(rot * math.pi / 180.0)
        global_rotation_matrix = np.matmul(
            global_rotation_matrix, vertical_rotation_matrix
        )

        for slot, module in parent.iter_children():
            if module is None:
                continue
            # rotation for slot
            slot = Orientation(slot)

            # Z-axis rotation
            slot_rotation = np.matmul(
                global_rotation_matrix, slot.get_slot_rotation_matrix()
            )

            # Do one step in the calculated direction
            movement = np.matmul(slot_rotation, step)

            # calculate new coordinate
            coordinates = (
                parent.substrate_coordinates[0] + movement[0][0],
                parent.substrate_coordinates[1] + movement[1][0],
                parent.substrate_coordinates[2] + movement[2][0],
            )
            module.substrate_coordinates = coordinates

            # For Karine: If you need to validate old robots, remember to add this condition to this if:
            # if raise_for_intersections and coordinates in substrate_coordinates_map and type(module)
            # is not TouchSensorModule:
            if raise_for_intersections:
                if coordinates in substrate_coordinates_map:
                    raise self.ItersectionCollisionException(substrate_coordinates_map)
                substrate_coordinates_map[coordinates] = module.id

            self._update_substrate(
                raise_for_intersections,
                module,
                slot_rotation,
                substrate_coordinates_map,
            )

    def iter_all_elements(self) -> Iterable[RevolveModule]:
        to_process = deque([self._body])
        while len(to_process) > 0:
            elem: RevolveModule = to_process.popleft()
            for _i, child in elem.iter_children():
                if child is not None:
                    to_process.append(child)
            yield elem

    def render_brain(self, img_path: str) -> None:
        """
        Render image of brain
        :param img_path: path to where to store image
        """
        if self._brain is None:
            raise RuntimeError("Brain not initialized")
        elif isinstance(self._brain, BrainNN):
            try:
                brain_graph = BrainGraph(self._brain, img_path)
                brain_graph.brain_to_graph(True)
                brain_graph.save_graph()
            except Exception as e:
                logger.exception("Failed rendering brain. Exception:")
        else:
            with open(img_path, "w") as file:
                file.write("dummy\n")
            logger.warn(
                "Brain {} image rendering not supported".format(type(self._brain))
            )

    def render_body(self, img_path: str) -> None:
        """
        Render 2d representation of robot and store as png
        :param img_path: path of storing png file
        """
        if self._body is None:
            raise RuntimeError("Body not initialized")
        else:
            try:
                render = Render()
                render.render_robot(self._body, img_path)
            except Exception as e:
                logger.exception("Failed rendering 2d robot")

    def __repr__(self):
        return f"RevolveBot({self.id})"
