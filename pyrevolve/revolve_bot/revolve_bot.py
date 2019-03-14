"""
Revolve body generator based on RoboGen framework
"""
import yaml
import math
from collections import OrderedDict

from pyrevolve import SDF

from .revolve_module import CoreModule
from .revolve_module import ActiveHingeModule
from .revolve_module import BrickModule
from .revolve_module import BrickSensorModule
from .revolve_module import Orientation
from .revolve_module import BoxSlot
from .brain_nn import BrainNN

import xml.etree.ElementTree


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
        pass

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

        if 'brain' in yaml_bot:
            yaml_brain = yaml_bot['brain']
            if 'type' not in yaml_brain:
                # raise IOError("brain type not defined, please fix it")
                brain_type = 'neural-network'
            else:
                brain_type = yaml_brain['type']

            if brain_type == 'neural-network':
                self._brain = BrainNN()
                self._brain.FromYaml(yaml_brain)

        else:
            self._brain = None

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
            robot = self.to_sdf()

        with open(path, 'w') as robot_file:
            robot_file.write(robot)

    def update_substrate(self):
        """
        Update all coordinates for body components

        :return:
        """
        return ''

    def render2d(self):
        """

        :return:
        """
        raise NotImplementedError("Render2D not yet implemented")
