from sdfbuilder import PosableGroup
from sdfbuilder.structure import Visual, Collision, Geometry


class Component(PosableGroup):
    """

    """

    def __init__(self, name, geometry, collision=True, visual=True):
        """
        :param name:
        :param geometry:
        :type geometry: Geometry
        :param collision:
        :param visual:
        :return:
        """
        super(Component, self).__init__(name)

        if visual:
            self.visual = Visual(name+"_visual", geometry.copy())
            self.add_element(self.visual)

        if collision:
            self.collision = Collision(name+"_collision", geometry.copy())
            self.add_element(self.collision)

        # List of connections from this component to other components
        self.connections = []
        """ :type : list[Connection] """

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
