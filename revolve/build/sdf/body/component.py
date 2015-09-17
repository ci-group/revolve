from sdfbuilder import PosableGroup
from sdfbuilder.structure import Visual, Collision, Geometry
from sdfbuilder.sensor import Sensor as SdfSensor
from ..sensor import Sensor


class Component(PosableGroup):
    """

    """

    def __init__(self, part_id, name, geometry, collision=True, visual=True):
        """

        :param part_id:
        :param name:
        :param geometry:
        :type geometry: Geometry
        :param collision:
        :param visual:
        :return:
        """
        super(Component, self).__init__(name)

        # Holds the list of sensors registered with this component
        self.part_id = part_id
        self.sensors = []

        if visual:
            if isinstance(visual, Geometry):
                self.visual = Visual(name+"_visual", visual.copy())
            elif isinstance(visual, Visual):
                self.visual = visual.copy()

                # Make sure the name is unique, or the visual might not get rendered
                # (it might collide with another within the same link)
                self.visual.name = name+"_"+self.visual.name
            else:
                self.visual = Visual(name+"_visual", geometry.copy())

            self.add_element(self.visual)

        if collision:
            self.collision = Collision(name+"_collision", geometry.copy())
            self.add_element(self.collision)

        # List of connections from this component to other components
        self.connections = []
        """ :type : list[Connection] """

    def add_sensor(self, sensor, sensor_type=None, prefix=True):
        """
        :param sensor:
        :type sensor: SdfSensor
        :param sensor_type:
        :type sensor_type: str
        :param prefix: Sensor names need to be unique within a model, so
                        by default the name of the SDF sensor is prefixed
                        with the component ID for convenience. Set this
                        parameter to `False` to disable this behavior.
        :type prefix: bool
        :return:
        """
        if prefix:
            sensor.name = "%s-%s" % (str(self.part_id), sensor.name)

        self.sensors.append((sensor, sensor_type))
        self.add_element(sensor)

    def get_plugin_sensors(self, link):
        """
        :return:
        """
        return [Sensor(self.part_id, link, sensor, sensor_type)
                for sensor, sensor_type in self.sensors]

    def create_connection(self, other, joint=None):
        """
        Creates a connection between this component and another
        component, possibly governed by a joint.

        :param other:
        :type other: Component
        :param joint:
        :type joint: ComponentJoint
        """
        self.create_connection_one_way(other, joint)
        other.create_connection_one_way(self, joint)

    def create_connection_one_way(self, other, joint=None):
        """
        Creates a one-way connection, only used internally.
        """
        self.connections.append(Connection(other, joint))


class Connection(object):
    """
    Connection class for node graph connections
    """

    def __init__(self, other, joint=None):
        self.other = other
        self.joint = joint
