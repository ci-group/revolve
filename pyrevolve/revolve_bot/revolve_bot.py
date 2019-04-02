"""
Revolve body generator based on RoboGen framework
"""
import yaml
from collections import OrderedDict

from pyrevolve import SDF

from .revolve_module import CoreModule, Orientation
from .brain import Brain, BrainNN, BrainRLPowerSplines

from .render.render import Render
from .measure import Measure


class RevolveBot:
    """
    Basic robot description class that contains robot's body and/or brain
    structures, ID and several other necessary parameters. Capable of reading
    a robot's sdf mode
    """

    def __init__(self, id=None):
        self._body = None
        self._brain = None
        self._id = id
        self._parents = None
        self._fitness = None
        self._behavioural_measurement = None
        self._battery_level = None

    @property
    def id(self):
        return self._id

    @property
    def body(self):
        return self._body

    @property
    def brain(self):
        return self._brain

    def size(self):
        robot_size = 1 + self._recursive_size_measurement(self._body)
        print("calculating robot size: {}".format(robot_size))
        return robot_size

    def _recursive_size_measurement(self, module):
        count = 0
        for _, child in module.iter_children():
            if child is not None:
                count += 1 + self._recursive_size_measurement(child)

        return count

    def measure_behaviour(self):
        """

        :return:
        """
        pass

    def measure_body(self):
        """
        :return:
        """
        try:
            measure = Measure(self._body)
            return measure.measure_all()
        except Exception as e:
            print('Exception: {}'.format(e))

    def measure_brain(self):
        """

        :return:
        """
        pass

    def load(self, text, conf_type):
        """
        Load robot's description from a string and parse it to Python structure
        :param text: Robot's description string
        :param conf_type: Type of a robot's description format
        :return:
        """
        if 'yaml' == conf_type:
            self.load_yaml(text)
        elif 'sdf' == conf_type:
            raise NotImplementedError("Loading from SDF not yet implemented")

    def load_yaml(self, text):
        """
        Load robot's description from a yaml string
        :param text: Robot's yaml description
        """
        yaml_bot = yaml.safe_load(text)
        self._id = yaml_bot['id'] if 'id' in yaml_bot else None
        self._body = CoreModule.FromYaml(yaml_bot['body'])

        try:
            if 'brain' in yaml_bot:
                yaml_brain = yaml_bot['brain']
                if 'type' not in yaml_brain:
                    # raise IOError("brain type not defined, please fix it")
                    yaml_brain['type'] = 'neural-network'
                self._brain = Brain.from_yaml(yaml_brain)
            else:
                self._brain = Brain()
        except:
            self._brain = Brain()
            print('Failed to load brain, setting to None')

    def load_file(self, path, conf_type='yaml'):
        """
        Read robot's description from a file and parse it to Python structure
        :param path: Robot's description file path
        :param conf_type: Type of a robot's description format
        :return:
        """
        with open(path, 'r') as robot_file:
            robot = robot_file.read()

        self.load(robot, conf_type)

    def to_sdf(self, pose=SDF.math.Vector3(0, 0, 0.25), nice_format=None):
        if type(nice_format) is bool:
            nice_format = '\t' if nice_format else None
        return SDF.revolve_bot_to_sdf(self, pose, nice_format)

    def to_yaml(self):
        """
        Converts robot data structure to yaml

        :return:
        """
        yaml_dict = OrderedDict()
        yaml_dict['id'] = self._id
        yaml_dict['body'] = self._body.to_yaml()
        if self._brain is not None:
            yaml_dict['brain'] = self._brain.to_yaml()

        return yaml.dump(yaml_dict)

    def save_file(self, path, conf_type='yaml'):
        """
        Save robot's description on a given file path in a specified format
        :param path:
        :param conf_type:
        :return:
        """
        robot = ''
        if 'yaml' == conf_type:
            robot = self.to_yaml()
        elif 'sdf' == conf_type:
            robot = self.to_sdf(nice_format=True)

        with open(path, 'w') as robot_file:
            robot_file.write(robot)

    def update_substrate(self, raise_for_intersections=False):
        """
        Update all coordinates for body components

        :param raise_for_intersections: enable raising an exception if a collision of coordinates is detected
        :raises self.ItersectionCollisionException: If a collision of coordinates is detected (and check is enabled)
        """
        substrate_coordinates_all = {(0, 0): self._body.id}
        self._body.substrate_coordinates = (0, 0)
        self._update_substrate(raise_for_intersections, self._body, Orientation.NORTH, substrate_coordinates_all)

    class ItersectionCollisionException(Exception):
        """
        A collision has been detected when updating the robot coordinates.
        Check self.substrate_coordinates_map to know more.
        """
        def __init__(self, substrate_coordinates_map):
            super().__init__(self)
            self.substrate_coordinates_map = substrate_coordinates_map

    def _update_substrate(self,
                          raise_for_intersections,
                          parent,
                          parent_direction,
                          substrate_coordinates_map):
        """
        Internal recursive function for self.update_substrate()
        :param raise_for_intersections: same as in self.update_substrate
        :param parent: updates the children of this parent
        :param parent_direction: the "absolute" orientation of this parent
        :param substrate_coordinates_map: map for all already explored coordinates(useful for coordinates conflict checks)
        """
        dic = {Orientation.NORTH: 0,
               Orientation.WEST:  1,
               Orientation.SOUTH: 2,
               Orientation.EAST:  3}
        inverse_dic = {0: Orientation.NORTH,
                       1: Orientation.WEST,
                       2: Orientation.SOUTH,
                       3: Orientation.EAST}

        movement_table = {
            Orientation.NORTH: ( 1,  0),
            Orientation.WEST:  ( 0, -1),
            Orientation.SOUTH: (-1,  0),
            Orientation.EAST:  ( 0,  1),
        }

        for slot, module in parent.iter_children():
            if module is None:
                continue

            slot = Orientation(slot)

            # calculate new direction
            direction = dic[parent_direction] + dic[slot]
            if direction >= len(dic):
                direction = direction - len(dic)
            new_direction = Orientation(inverse_dic[direction])

            # calculate new coordinate
            movement = movement_table[new_direction]
            coordinates = (
                parent.substrate_coordinates[0] + movement[0],
                parent.substrate_coordinates[1] + movement[1],
            )
            module.substrate_coordinates = coordinates

            # For Karine: If you need to validate old robots, remember to add this condition to this if:
            # if raise_for_intersections and coordinates in substrate_coordinates_all and type(module) is not TouchSensorModule:
            if raise_for_intersections:
                if coordinates in substrate_coordinates_map:
                    raise self.ItersectionCollisionException(substrate_coordinates_map)
                substrate_coordinates_map[coordinates] = module.id

            self._update_substrate(raise_for_intersections,
                                   module,
                                   new_direction,
                                   substrate_coordinates_map)

    def render2d(self, img_path):
        """
        Render 2d representation of robot and store as png
        :param img_path: path of storing png file
        """
        if self._body is None:
            raise RuntimeError('Body not initialized')
        else:
            try:
                render = Render()
                render.render_robot(self._body, img_path)
            except:
                print('Failed rendering 2d robot')
