"""
Class containing the body parts to compose a Robogen robot
"""
from collections import OrderedDict
from enum import Enum

from pyrevolve.sdfbuilder import Link
from pyrevolve.sdfbuilder import math as SDFmath
from pyrevolve.sdfbuilder.structure import Box
from pyrevolve.sdfbuilder.structure import Collision
from pyrevolve.sdfbuilder.structure import Visual
from pyrevolve.sdfbuilder.structure import Mesh
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
    SOUTH = 0
    NORTH = 1
    EAST = 2
    WEST = 3

    def short_repr(self):
        if self == self.SOUTH:
            return 'S'
        elif self == self.NORTH:
            return 'N'
        elif self == self.EAST:
            return 'E'
        elif self == self.WEST:
            return 'W'


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
        for i, child in enumerate(self.children):
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

    def to_sdf(self, tree_depth):
        """

        :return:
        """
        return self._brick_to_sdf(tree_depth)

    def _brick_to_sdf(self, tree_depth=''):
        name = 'component_{}_{}__box'.format(tree_depth, self.TYPE)
        visual = SDF.Visual(name)
        geometry = SDF.MeshGeometry(self.VISUAL_MESH)
        visual.append(geometry)

        collision = SDF.Collision(name, self.MASS)
        geometry = SDF.BoxGeometry(self.COLLISION_BOX)
        collision.append(geometry)

        return visual, collision

    def boxslot(self, orientation=None):
        orientation = Orientation.SOUTH if orientation is None else orientation
        return BoxSlot(self.possible_slots(), orientation)

    def possible_slots(self):
        box_geometry = self.COLLISION_BOX
        return (
            (box_geometry[0] / -2.0, box_geometry[0] / 2.0),  # X
            (box_geometry[1] / -2.0, box_geometry[1] / 2.0),  # Y
            (box_geometry[2] / -2.0, box_geometry[2] / 2.0),  # Z
        )


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

    def to_sdf_old(self):
        """
        Converts the CoreComponent to SDF format
        :return:
        """
        # TODO: Scale needs to be checked
        scale = 0.5
        mesh = Mesh(
            uri="model://rg_robot/meshes/CoreComponent.dae",
            scale=scale
        )

        visual = Visual(name="visual_{}".format(self.id), geometry=mesh)
        collision = Collision(
            name="collision_{}".format(self.id),
            geometry=Box(1.0, 1.0, 1.0, mass=0.3)
        )

        link = Link(
            name="link_{}".format(self.id),
            self_collide=True,
            elements=[visual, collision]
        )
        rgb = self.color()
        link.make_color(r=rgb[0], g=rgb[1], b=rgb[2], a=1.0)

        return link

    def possible_slots(self):
        return (
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # X
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # Y
            (-self.SLOT_COORDINATES, self.SLOT_COORDINATES),  # Z
        )


class ActiveHingeModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen joint module
    """
    TYPE = 'ActiveHinge'
    VISUAL_MESH_FRAME = 'model://rg_robot/meshes/ActiveHinge_Frame.dae'
    VISUAL_MESH_SERVO = 'model://rg_robot/meshes/ActiveCardanHinge_Servo_Holder.dae'
    COLLISION_BOX_FRAME = (2.20e-02, 3.575e-02, 1.0e-02)
    COLLISION_BOX_SERVO = (2.45e-02, 2.575e-02, 1.5e-02)
    # COLLISION_BOX_SERVO = (2.925000e-02, 3.400000e-02, 1.000000e-02)
    COLLISION_BOX_SERVO_OFFSET = (
        SDFmath.Vector3(0, 0, 0),
        SDFmath.Vector3(-0.0091, 0, 0),
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

    def to_sdf(self, tree_depth):
        name_frame = 'component_{}_{}__frame'.format(tree_depth, self.TYPE)
        name_servo = 'component_{}_{}__servo'.format(tree_depth, self.TYPE)

        # offset = SDFmath.Vector3(self.COLLISION_BOX_FRAME[0] / 2)

        visual_frame = SDF.Visual(name_frame)
        geometry = SDF.MeshGeometry(self.VISUAL_MESH_FRAME)
        visual_frame.append(geometry)

        collision_frame = SDF.Collision(name_frame, self.MASS_FRAME)
        geometry = SDF.BoxGeometry(self.COLLISION_BOX_FRAME)
        collision_frame.append(geometry)

        visual_servo = SDF.Visual(name_servo)
        geometry = SDF.MeshGeometry(self.VISUAL_MESH_SERVO)
        visual_servo.append(geometry)

        collision_servo = SDF.Collision(name_servo, self.MASS_SERVO)
        collision_servo.translate(SDFmath.Vector3(0.002375, 0, 0))
        geometry = SDF.BoxGeometry(self.COLLISION_BOX_SERVO)
        collision_servo.append(geometry)

        # TODO
        joint = None

        return visual_frame, collision_frame, \
               visual_servo, collision_servo, \
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
        orientation = Orientation.SOUTH if orientation is None else orientation
        boundaries = self.possible_slots_frame()
        return BoxSlotJoints(
            boundaries,
            orientation,
            self.COLLISION_BOX_SERVO_OFFSET
        )

    def boxslot_servo(self, orientation=None):
        orientation = Orientation.SOUTH if orientation is None else orientation
        boundaries = self.possible_slots_servo()
        return BoxSlotJoints(boundaries, orientation)

    def boxslot(self, orientation=None):
        orientation = Orientation.SOUTH if orientation is None else orientation
        if orientation is Orientation.SOUTH:
            return self.boxslot_frame(orientation)
        elif orientation is Orientation.NORTH:
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
    Inherits class RevolveModule. Creates Robogen brick sensor module
    """
    TYPE = "FixedBrickSensor"

    def __init__(self):
        super().__init__()


class TouchSensorModule(RevolveModule):
    """
    Inherits class RevolveModule. Creates Robogen sensor module
    """
    TYPE = "TouchSensor"
    MASS = grams(3)

    def __init__(self):
        super().__init__()


class BoxSlot:
    def __init__(self, boundaries, orientation: Orientation):
        self.orientation = orientation
        self.pos = self._calculate_box_slot_pos(boundaries, orientation)
        self.normal = self.pos.normalized()
        self.tangent = self._calculate_box_slot_tangent(orientation)

    def _calculate_box_slot_pos(self, boundaries, slot: Orientation):
        # boundaries = collision_elem.boundaries
        if slot == Orientation.SOUTH:
            return SDFmath.Vector3(0, boundaries[1][0], 0)
        elif slot == Orientation.NORTH:
            return SDFmath.Vector3(0, boundaries[1][1], 0)
        elif slot == Orientation.EAST:
            return SDFmath.Vector3(boundaries[0][1], 0, 0)
        elif slot == Orientation.WEST:
            return SDFmath.Vector3(boundaries[0][0], 0, 0)
        else:
            raise RuntimeError('invalid module orientation: {}'.format(slot))

    @staticmethod
    def _calculate_box_slot_tangent(slot: Orientation):
        """
        Return slot tangent
        """
        if slot == Orientation.SOUTH:
            return SDFmath.Vector3(0, 0, 1)
        elif slot == Orientation.NORTH:
            return SDFmath.Vector3(0, 0, 1)
        elif slot == Orientation.EAST:
            return SDFmath.Vector3(0, 0, 1)
        elif slot == Orientation.WEST:
            return SDFmath.Vector3(0, 0, 1)
        # elif slot == 4:
        #     # Right face tangent: back face
        #     return SDFmath.Vector3(0, 1, 0)
        # elif slot == 5:
        #     # Left face tangent: back face
        #     return SDFmath.Vector3(0, 1, 0)
        else:
            raise RuntimeError("Invalid orientation")


class BoxSlotJoints(BoxSlot):

    def __init__(self, boundaries, orientation: Orientation, offset=(SDFmath.Vector3(), SDFmath.Vector3())):
        self.offset = offset
        super().__init__(boundaries, orientation)

    def _calculate_box_slot_pos(self, boundaries, slot: Orientation):
        # boundaries = collision_elem.boundaries
        if slot == Orientation.SOUTH:
            return SDFmath.Vector3(boundaries[0][0], 0, 0) + self.offset[0]
            # return SDFmath.Vector3(0, boundaries[0][0], 0)
        elif slot == Orientation.NORTH:
            return SDFmath.Vector3(boundaries[0][1], 0, 0) + self.offset[1]
            # return SDFmath.Vector3(0, boundaries[0][1], 0)
        else:
            raise RuntimeError('invalid module orientation: {}'.format(slot))

    @staticmethod
    def _calculate_box_slot_tangent(slot: Orientation):
        """
        Return slot tangent
        """
        if slot == Orientation.SOUTH:
            return SDFmath.Vector3(0, 0, 1)
        elif slot == Orientation.NORTH:
            return SDFmath.Vector3(0, 0, 1)
        else:
            raise RuntimeError("Invalid orientation")
