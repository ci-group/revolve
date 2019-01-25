"""
Class containing the body parts to compose a Robogen robot
"""


class RevolveModule():
    """
    Base class allowing for constructing Robogen components in an overviewable manner
    """

    def __init__(self):
        self.id = None
        self.type = None
        self.children = [None]
        self.orientation = None
        self.colour = {"r": 0, "g": 0, "b": 0}
        self.substrate_coordinates = None

    def to_sdf(self):
        """

        :return:
        """

        return ''


class CoreModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen core module
    """
    def __init__(self):
        super(RevolveModule, self).__init__()


class JointModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen joint module
    """
    def __init__(self):
        super(RevolveModule, self).__init__()


class BrickModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen brick module
    """
    def __init__(self):
        super(RevolveModule, self).__init__()


class BrickSensorModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen brick sensor module
    """
    def __init__(self):
        super(RevolveModule, self).__init__()

