from collections.abc import Iterable
from enum import Enum
from pyrevolve.custom_logging.logger import logger

INDEX_SYMBOL = 0
INDEX_PARAMS = 1


class Alphabet(Enum):
    # Modules
    CORE_COMPONENT = 'C'
    JOINT_HORIZONTAL = 'AJ1'
    JOINT_VERTICAL = 'AJ2'
    BLOCK = 'B'
    BLOCK_VERTICAL = 'BV'
    SENSOR = 'ST'

    # MorphologyMountingCommands
    ADD_RIGHT = 'addr'
    ADD_FRONT = 'addf'
    ADD_LEFT = 'addl'

    # MorphologyMovingCommands
    MOVE_RIGHT = 'mover'
    MOVE_FRONT = 'movef'
    MOVE_LEFT = 'movel'
    MOVE_BACK = 'moveb'
    ROTATE_90 = 'rotate90'
    ROTATE_N90 = 'rotaten90'
    PUSH_MOV_STACK = '('
    POP_MOV_STACK = ')'

    # ControllerChangingCommands
    ADD_EDGE = 'brainedge'
    MUTATE_EDGE = 'brainperturb'
    LOOP = 'brainloop'
    MUTATE_AMP = 'brainampperturb'
    MUTATE_PER = 'brainperperturb'
    MUTATE_OFF = 'brainoffperturb'

    # ControllerMovingCommands
    MOVE_REF_S = 'brainmoveFTS'
    MOVE_REF_O = 'brainmoveTTS'

    @staticmethod
    def modules(allow_vertical_brick: bool):
        # this function MUST return the core always as the first element
        modules = [
            Alphabet.CORE_COMPONENT,
            Alphabet.JOINT_HORIZONTAL,
            Alphabet.JOINT_VERTICAL,
            Alphabet.BLOCK,
            Alphabet.SENSOR,
        ]
        if allow_vertical_brick:
            modules.append(Alphabet.BLOCK_VERTICAL)
        return modules

    def is_vertical_module(self):
        return self is Alphabet.JOINT_VERTICAL \
               or self is Alphabet.BLOCK_VERTICAL

    @staticmethod
    def morphology_mounting_commands():
        return [
            Alphabet.ADD_RIGHT,
            Alphabet.ADD_FRONT,
            Alphabet.ADD_LEFT,
        ]

    @staticmethod
    def morphology_moving_commands(use_movement_commands: bool, use_rotation_commands: bool, use_movement_stack: bool):
        commands = []
        if use_movement_commands:
            commands.append(Alphabet.MOVE_RIGHT)
            commands.append(Alphabet.MOVE_FRONT)
            commands.append(Alphabet.MOVE_LEFT)
            commands.append(Alphabet.MOVE_BACK)
        if use_rotation_commands:
            commands.append(Alphabet.ROTATE_90)
            commands.append(Alphabet.ROTATE_N90)
        if use_movement_stack:
            commands.append(Alphabet.PUSH_MOV_STACK)
            commands.append(Alphabet.POP_MOV_STACK)

        if len(commands) == 0:
            logger.warning("NO MOVEMENT COMMAND IS CONFIGURED - this could be a problem")

        return commands

    @staticmethod
    def controller_changing_commands():
        return [
            Alphabet.ADD_EDGE,
            Alphabet.MUTATE_EDGE,
            Alphabet.LOOP,
            Alphabet.MUTATE_AMP,
            Alphabet.MUTATE_PER,
            Alphabet.MUTATE_OFF,
        ]

    @staticmethod
    def controller_moving_commands():
        return [
            Alphabet.MOVE_REF_S,
            Alphabet.MOVE_REF_O,
        ]

    @staticmethod
    def wordify(letters):
        if isinstance(letters, Iterable):
            return [(a, []) for a in letters]
        else:
            return (letters, [])
