"""
Class containing the body parts to compose a Robogen robot
"""
import math
from collections import OrderedDict
from enum import Enum
import numpy as np

from pyrevolve import SDF


# MEASUREMENT CONVERSION
def mm(x):
    return x / 1000.0


def cm(x):
    return x / 100.0


def grams(x):
    return x / 1000.0


# Module Orientation
class Orientation(Enum):
    BACK = 0
    FORWARD = 1
    LEFT = 2
    RIGHT = 3

    def short_repr(self):
        if self == self.BACK:
            return 'B'
        elif self == self.FORWARD:
            return 'F'
        elif self == self.LEFT:
            return 'L'
        elif self == self.RIGHT:
            return 'R'
        else:
            assert False

    def get_slot_rotation_matrix(self):
        if self == self.BACK:
            return rotate_matrix_z_axis(math.pi) # 180
        elif self == self.FORWARD:
            return rotate_matrix_z_axis(0.0)
        elif self == self.LEFT:
            return rotate_matrix_z_axis(math.pi / 2.0) # 90
        elif self == self.RIGHT:
            return rotate_matrix_z_axis(math.pi / -2.0) # -90


def rotate_matrix_z_axis(angle):
    z_rotation_matrix = np.array([
        [round(np.cos(angle)), -1*round(np.sin(angle)), 0],
        [round(np.sin(angle)),    round(np.cos(angle)), 0],
        [0,                                          0, 1]
        ])

    return z_rotation_matrix


def rotate_matrix_x_axis(angle):
    x_rotation_matrix = np.array([
        [1,                      0,                       0],
        [0,   round(np.cos(angle)), -1*round(np.sin(angle))],
        [0,   round(np.sin(angle)),    round(np.cos(angle))]
    ])

    return x_rotation_matrix


class RevolveModule:
    """
    Base class allowing for constructing Robogen components in an overviewable manner
    """
    DEFAULT_COLOR = (0.5, 0.5, 0.5)
    TYPE = None
    VISUAL_MESH = None
    COLLISION_BOX = None
    MASS = None
    INERTIA = None

    def __init__(self):
        self.id = None
        self.orientation = None
        self.rgb = None  # RevolveModule.DEFAULT_COLOR
        self.substrate_coordinates = None
        self.children = [None, None, None, None]
        self.info = None

    def color(self):
        return self.rgb if self.rgb is not None else self.DEFAULT_COLOR

    @staticmethod
    def FromYaml(yaml_object):
        """
        From a yaml object, creates a data struture of interconnected body modules. 
        Standard names for modules are: 
        CoreComponent
        ActiveHinge
        FixedBrick
        FixedBrickSensor
        """
        mod_type = yaml_object['type']
        if mod_type == 'CoreComponent' or mod_type == 'Core':
            module = CoreModule()
        elif mod_type == 'ActiveHinge':
            module = ActiveHingeModule()
        elif mod_type == 'FixedBrick':
            module = BrickModule()
        elif mod_type == 'FixedBrickSensor':
            module = BrickSensorModule()
        elif mod_type == 'TouchSensor':
            module = TouchSensorModule()
        else:
            raise NotImplementedError('"{}" module not yet implemented'.format(mod_type))

        module.id = yaml_object['id']

        try:
            module.orientation = yaml_object['orientation']
        except KeyError:
            module.orientation = 0

        try:
            module.rgb = (
                yaml_object['params']['red'],
                yaml_object['params']['green'],
                yaml_object['params']['blue'],
            )
        except KeyError:
            pass

        if 'children' in yaml_object:
            for parent_slot in yaml_object['children']:
                module.children[parent_slot] = RevolveModule.FromYaml(
                    yaml_object=yaml_object['children'][parent_slot])

        return module

    def to_yaml(self):
        if self.TYPE is None:
            raise RuntimeError('Module TYPE is not implemented for "{}",'
                               ' this should be defined.'.format(self.__class__))

        yaml_dict_object = OrderedDict()
        yaml_dict_object['id'] = self.id
        yaml_dict_object['type'] = self.TYPE
        yaml_dict_object['orientation'] = self.orientation

        if self.rgb is not None:
            yaml_dict_object['params'] = {
                'red': self.rgb[0],
                'green': self.rgb[1],
                'blue': self.rgb[2],
            }

        children = self._generate_yaml_children()
        if children is not None:
            yaml_dict_object['children'] = children

        return yaml_dict_object

    def iter_children(self):
        return enumerate(self.children)

    def _generate_yaml_children(self):
        has_children = False

        children = {}
        for i, child in self.iter_children():
            if child is not None:
                children[i] = child.to_yaml()
                has_children = True

        return children if has_children else None

    def validate(self):
        """
        Tests if the robot tree is valid (recursively)
        :return: True if the robot tree is valid
        """
        raise RuntimeError("Robot tree validation not yet implemented")

    def to_sdf(self, tree_depth='', parent_link=None, child_link=None):
        """
        Transform the module in sdf elements.

        IMPORTANT: It does not append VISUAL and COLLISION elements to the parent link
        automatically. It does append automatically the SENSOR element.
        TODO: make the append automatic for VISUAL AND COLLISION AS WELL.

        :param tree_depth: current tree depth as string (for naming)
        :param parent_link: link of the parent (may be needed for certain modules)
        :param child_link: link of the child (may be needed for certain modules, like hinges)
        :return: visual SDF element, collision SDF element, sensor SDF element.
        Sensor SDF element may be None.
        """
        name = 'component_{}_{}__box'.format(tree_depth, self.TYPE)
        visual = SDF.Visual(name, self.rgb)
        geometry = SDF.MeshGeometry(self.VISUAL_MESH)
        visual.append(geometry)

        collision = SDF.Collision(name, self.MASS)
        geometry = SDF.BoxGeometry(self.COLLISION_BOX)
        collision.append(geometry)

        return visual, collision, None

    def boxslot(self, orientation=None):
        orientation = Orientation.BACK if orientation is None else orientation
        return BoxSlot(self.possible_slots(), orientation)

    def possible_slots(self):
        box_geometry = self.COLLISION_BOX
        return (
            (box_geometry[0] / -2.0, box_geometry[0] / 2.0),  # X
            (box_geometry[1] / -2.0, box_geometry[1] / 2.0),  # Y
            (box_geometry[2] / -2.0, box_geometry[2] / 2.0),  # Z
        )

    def has_children(self):
        """
        Check wheter module has children
        :return: True if module has children
        """
        has_children = False

        if self.children == {1: None}: return False

        for i, child in enumerate(self.children):
            if child is not None:
                has_children = True

        return has_children


class CoreModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen core module
    """
    TYPE = "CoreComponent"
    VISUAL_MESH = 'model://rg_robot/meshes/CoreComponent.dae'
    SLOT_COORDINATES = 0.089 / 2.0
    COLLISION_BOX = (0.089, 0.089, 0.045)
    MASS = grams(90)

    def __init__(self):
        super().__init__()
        self.substrate_coordinates = (0, 0, 0)

    def possible_slots(self):
        return (
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # X
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # Y
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # Z
        )

    def to_sdf(self, tree_depth='', parent_link=None, child_link=None):
        imu_sensor = SDF.IMUSensor('core-imu_sensor', parent_link, self)
        visual, collision, _ = super().to_sdf(tree_depth, parent_link, child_link)
        parent_link.append(imu_sensor)
        return visual, collision, imu_sensor


class ActiveHingeModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen joint module
    """
    TYPE = 'ActiveHinge'
    VISUAL_MESH_FRAME = 'model://rg_robot/meshes/ActiveHinge_Frame.dae'
    VISUAL_MESH_SERVO = 'model://rg_robot/meshes/ActiveCardanHinge_Servo_Holder.dae'
    COLLISION_BOX_FRAME = (2.20e-02, 3.575e-02, 1.0e-02)
    COLLISION_BOX_SERVO = (2.45e-02, 2.575e-02, 1.5e-02)
    COLLISION_BOX_SERVO_2 = (1.0e-3, 3.4e-2, 3.4e-02)
    COLLISION_BOX_SERVO_OFFSET = (
        SDF.math.Vector3(0, 0, 0),
        SDF.math.Vector3(-0.0091, 0, 0),
    )
    MASS_FRAME = grams(1.7)
    MASS_SERVO = grams(9)

    def __init__(self):
        super().__init__()
        self.children = {1: None}

    def iter_children(self):
        return self.children.items()

    def _generate_yaml_children(self):
        child = self.children[1]
        if child is None:
            return None
        else:
            return {1: child.to_yaml()}

    def to_sdf(self, tree_depth='', parent_link=None, child_link=None):
        assert(parent_link is not None)
        assert(child_link is not None)
        name_frame = 'component_{}_{}__frame'.format(tree_depth, self.TYPE)
        name_joint = 'component_{}_{}__joint'.format(tree_depth, self.TYPE)
        name_servo = 'component_{}_{}__servo'.format(tree_depth, self.TYPE)
        name_servo2 = 'component_{}_{}__servo2'.format(tree_depth, self.TYPE)

        visual_frame = SDF.Visual(name_frame, self.rgb)
        geometry = SDF.MeshGeometry(self.VISUAL_MESH_FRAME)
        visual_frame.append(geometry)

        collision_frame = SDF.Collision(name_frame, self.MASS_FRAME)
        geometry = SDF.BoxGeometry(self.COLLISION_BOX_FRAME)
        collision_frame.append(geometry)

        visual_servo = SDF.Visual(name_servo, self.rgb)
        geometry = SDF.MeshGeometry(self.VISUAL_MESH_SERVO)
        visual_servo.append(geometry)

        collision_servo = SDF.Collision(name_servo, self.MASS_SERVO)
        collision_servo.translate(SDF.math.Vector3(0.002375, 0, 0))
        geometry = SDF.BoxGeometry(self.COLLISION_BOX_SERVO)
        collision_servo.append(geometry)

        collision_servo_2 = SDF.Collision(name_servo2, 0)
        collision_servo_2.translate(SDF.math.Vector3(0.01175, 0.001, 0))
        geometry = SDF.BoxGeometry(self.COLLISION_BOX_SERVO_2)
        collision_servo_2.append(geometry)

        joint = SDF.Joint(self.id,
                          name_joint,
                          parent_link,
                          child_link,
                          axis=SDF.math.Vector3(0, 1, 0),
                          coordinates=self.substrate_coordinates,
                          motorized=True)

        joint.set_position(SDF.math.Vector3(-0.0085, 0, 0))

        return visual_frame, \
               [collision_frame], \
               visual_servo, \
               [collision_servo, collision_servo_2], \
               joint

    def possible_slots_frame(self):
        box_geometry = self.COLLISION_BOX_FRAME
        return (
            (box_geometry[0] / -2.0, box_geometry[0] / 2.0 - 0.001),  # X
            (0, 0),  # Y
            (0, 0),  # Z
        )

    def possible_slots_servo(self):
        box_geometry = self.COLLISION_BOX_SERVO
        return (
            (box_geometry[0] / -2.0, box_geometry[0] / 2.0),  # X
            (0, 0),  # Y
            (0, 0),  # Z
        )

    def boxslot_frame(self, orientation=None):
        orientation = Orientation.BACK if orientation is None else orientation
        boundaries = self.possible_slots_frame()
        return BoxSlotJoints(
            boundaries,
            orientation,
            self.COLLISION_BOX_SERVO_OFFSET
        )

    def boxslot_servo(self, orientation=None):
        orientation = Orientation.BACK if orientation is None else orientation
        boundaries = self.possible_slots_servo()
        return BoxSlotJoints(boundaries, orientation)

    def boxslot(self, orientation=None):
        orientation = Orientation.BACK if orientation is None else orientation
        if orientation is Orientation.BACK:
            return self.boxslot_frame(orientation)
        elif orientation is Orientation.FORWARD:
            return self.boxslot_servo(orientation)
        else:
            raise RuntimeError("Invalid orientation")


class BrickModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen brick module
    """
    TYPE = "FixedBrick"
    VISUAL_MESH = 'model://rg_robot/meshes/FixedBrick.dae'
    SLOT_COORDINATES = 3.8e-2 / 2.0
    COLLISION_BOX = (4.1e-2, 4.1e-2, 3.55e-02)
    MASS = grams(10.2)

    def __init__(self):
        super().__init__()

    def possible_slots(self):
        return (
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # X
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # Y
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # Z
        )


class BrickSensorModule(RevolveModule):
    """
    TODO not finished
    Inherits class RevolveModule. Creates Robogen brick sensor module
    """
    TYPE = "FixedBrickSensor"
    VISUAL_MESH = 'model://rg_robot/meshes/FixedBrick.dae'
    COLLISION_BOX = (4.1e-2, 4.1e-2, 3.55e-02)

    def __init__(self):
        super().__init__()
        raise RuntimeError("Not implemented yet")


class TouchSensorModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen sensor module
    """
    TYPE = "TouchSensor"
    VISUAL_MESH = 'model://rg_robot/meshes/TouchSensor.dae'
    SLOT_COORDINATES = 1e-2 / 2.0
    COLLISION_BOX = (4.1e-3, 3.1e-2, 1.55e-02)
    MASS = grams(3)

    def __init__(self):
        super().__init__()
        self.children = {}

    def boxslot(self, orientation=None):
        orientation = Orientation.BACK if orientation is None else orientation
        assert (orientation is Orientation.BACK)
        return BoxSlotTouchSensor(self.possible_slots())

    def possible_slots(self):
        return (
            (-self.SLOT_COORDINATES, 0),  # X
            (0, 0),  # Y
            (0, 0),  # Z
        )

    def to_sdf(self, tree_depth='', parent_link=None, child_link=None):
        assert(parent_link is not None)
        name = 'component_{}_{}'.format(tree_depth, self.TYPE)
        name_sensor = 'sensor_{}_{}'.format(tree_depth, self.TYPE)

        visual = SDF.Visual(name, self.rgb)
        geometry = SDF.MeshGeometry(self.VISUAL_MESH)
        visual.append(geometry)

        collision = SDF.Collision(name, self.MASS)
        geometry = SDF.BoxGeometry(self.COLLISION_BOX)
        # collision.translate(SDF.math.Vector3(0.01175, 0.001, 0))
        collision.append(geometry)

        sensor = SDF.TouchSensor(name_sensor, collision, parent_link, self)
        parent_link.append(sensor)

        return visual, collision, sensor


class BoxSlot:
    """
    Helper class for modules connection slots
    """
    def __init__(self, boundaries, orientation: Orientation):
        self.orientation = orientation
        self.pos = self._calculate_box_slot_pos(boundaries, orientation)
        self.normal = self.pos.normalized()
        self.tangent = self._calculate_box_slot_tangent(orientation)

    def _calculate_box_slot_pos(self, boundaries, slot: Orientation):
        # boundaries = collision_elem.boundaries
        if slot == Orientation.BACK:
            return SDF.math.Vector3(0, boundaries[1][0], 0)
        elif slot == Orientation.FORWARD:
            return SDF.math.Vector3(0, boundaries[1][1], 0)
        elif slot == Orientation.LEFT:
            return SDF.math.Vector3(boundaries[0][1], 0, 0)
        elif slot == Orientation.RIGHT:
            return SDF.math.Vector3(boundaries[0][0], 0, 0)
        else:
            raise RuntimeError('invalid module orientation: {}'.format(slot))

    @staticmethod
    def _calculate_box_slot_tangent(slot: Orientation):
        """
        Return slot tangent
        """
        if slot == Orientation.BACK:
            return SDF.math.Vector3(0, 0, 1)
        elif slot == Orientation.FORWARD:
            return SDF.math.Vector3(0, 0, 1)
        elif slot == Orientation.LEFT:
            return SDF.math.Vector3(0, 0, 1)
        elif slot == Orientation.RIGHT:
            return SDF.math.Vector3(0, 0, 1)
        # elif slot == 4:
        #     # Right face tangent: back face
        #     return SDF.math.Vector3(0, 1, 0)
        # elif slot == 5:
        #     # Left face tangent: back face
        #     return SDF.math.Vector3(0, 1, 0)
        else:
            raise RuntimeError("Invalid orientation")


class BoxSlotJoints(BoxSlot):

    def __init__(self, boundaries, orientation: Orientation, offset=(SDF.math.Vector3(), SDF.math.Vector3())):
        self.offset = offset
        super().__init__(boundaries, orientation)

    def _calculate_box_slot_pos(self, boundaries, slot: Orientation):
        if slot == Orientation.BACK:
            return SDF.math.Vector3(boundaries[0][0], 0, 0) + self.offset[0]
        elif slot == Orientation.FORWARD:
            return SDF.math.Vector3(boundaries[0][1], 0, 0) + self.offset[1]
        else:
            raise RuntimeError('invalid module orientation: {}'.format(slot))

    @staticmethod
    def _calculate_box_slot_tangent(slot: Orientation):
        """
        Return slot tangent
        """
        if slot == Orientation.BACK:
            return SDF.math.Vector3(0, 0, 1)
        elif slot == Orientation.FORWARD:
            return SDF.math.Vector3(0, 0, 1)
        else:
            raise RuntimeError("Invalid orientation")


class BoxSlotTouchSensor(BoxSlot):
    def __init__(self, boundaries):
        super().__init__(boundaries, Orientation.BACK)

    def _calculate_box_slot_pos(self, boundaries, slot: Orientation):
        if slot == Orientation.BACK:
            return SDF.math.Vector3(boundaries[0][0], 0, 0)
        else:
            raise RuntimeError('invalid module orientation: {}'.format(slot))

    @staticmethod
    def _calculate_box_slot_tangent(slot: Orientation):
        """
        Return slot tangent
        """
        if slot == Orientation.BACK:
            return SDF.math.Vector3(0, 1, 0)
        else:
            raise RuntimeError("Invalid orientation")
