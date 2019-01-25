"""
Revolve body generator based on RoboGen framework
"""


class RevolveBot():
    """
    Basic robot description class that contains robot's body and/or brain
    structures, ID and several other necessary parameters. Capable of reading
    a robot's sdf mode
    """

    def __init__(self, id=None):
        self._body = None
        self._brain = None
        self._id = id
        self._parents = [None, None]
        self._fitness = None
        self._behaviour = None

    def describe_behaviour(self):
        """

        :return:
        """
        pass

    def describe_body(self):
        """

        :return:
        """
        pass

    def describe_brain(self):
        """

        :return:
        """
        pass

    def load(self, robot, type='yaml'):
        """
        Load robot's description from a string and parse it to Python structure
        :param robot: Robot's description string
        :param type: Type of a robot's description format
        :return:
        """
        if 'yaml' == type:
            pass
        elif 'protobuf' == type:
            pass

    def read(self, path, type='yaml'):
        """
        Read robot's description from a file and parse it to Python structure
        :param path: Robot's description file path
        :param type: Type of a robot's description format
        :return:
        """
        with open(path, 'r') as robot_file:
            robot = robot_file.read()

        self.load(robot, type)

    def render2d(self):
        """

        :return:
        """
        pass

    def save(self, path, type='yaml'):
        """
        Save robot's description on a given file path in a specified format
        :param path:
        :param type:
        :return:
        """
        robot = ''
        if 'proto' == type:
            robot = self.to_yaml()
        elif 'yaml' == type:
            robot = self.to_yaml()
        elif 'sdf' == type:
            robot = self.to_sdf()

        with open(path, 'w') as robot_file:
            robot_file.write(robot)

    def to_proto(self):
        """
        We wouln't use proto anymore here, right?
        :return:
        """
        return ''

    def to_sdf(self):
        """
        Converts yaml to sdf

        :return:
        """
        return ''

    def to_yaml(self):
        """
        Converts sdf to yaml

        :return:
        """
        return ''

    def update_substrate(self):
        """

        :return:
        """
        return ''

