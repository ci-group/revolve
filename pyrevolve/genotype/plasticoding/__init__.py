from .alphabet import Alphabet
from .initialization import random_initialization
from .plasticoding import Plasticoding


class PlasticodingConfig:
    def __init__(self,
                 initialization_genome=random_initialization,
                 e_max_groups=3,
                 oscillator_param_min=1,
                 oscillator_param_max=10,
                 weight_param_min=-1,
                 weight_param_max=1,
                 weight_min=-1,
                 weight_max=1,
                 axiom_w=Alphabet.CORE_COMPONENT,
                 i_iterations=3,
                 max_structural_modules=100,
                 robot_id=0,
                 allow_linear_joint=True,
                 allow_vertical_brick=True,
                 use_movement_commands=True,
                 use_rotation_commands=True,
                 use_movement_stack=True,
                 allow_joint_joint_attachment=True,
                 ):
        self.allow_joint_joint_attachment = allow_joint_joint_attachment
        self.initialization_genome = initialization_genome
        self.e_max_groups = e_max_groups
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.weight_param_min = weight_param_min
        self.weight_param_max = weight_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.axiom_w = axiom_w
        self.i_iterations = i_iterations
        self.max_structural_modules = max_structural_modules
        self.robot_id = robot_id
        self.allow_vertical_brick = allow_vertical_brick
        self.allow_linear_joint = allow_linear_joint
        self.use_movement_commands = use_movement_commands
        self.use_rotation_commands = use_rotation_commands
        self.use_movement_stack = use_movement_stack
