from __future__ import annotations
from collections.abc import Iterable
from enum import Enum
from pyrevolve.custom_logging.logger import logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Union

INDEX_SYMBOL = 0
INDEX_PARAMS = 1


class Alphabet(Enum):
    # Modules
    CORE_COMPONENT = 'C'
    JOINT_HORIZONTAL = 'AJ1'
    JOINT_VERTICAL = 'AJ2'
    BLOCK = 'B'
    BLOCK1 = 'B1'
    BLOCK2 = 'B2'
    BLOCK3 = 'B3'
    BLOCK4 = 'B4'
    BLOCK_VERTICAL = 'BV'
    SENSOR = 'ST'

    # MorphologyMountingCommands
    ADD_RIGHT = 'addr'
    ADD_FRONT = 'addf'
    ADD_LEFT = 'addl'
    ADD_BACK = 'addb'

    # MorphologyMovingCommands
    MOVE_RIGHT = 'mover'
    MOVE_FRONT = 'movef'
    MOVE_LEFT = 'movel'
    MOVE_BACK = 'moveb'
    MOVE_NONE = 'moven'
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
    def modules(allow_vertical_brick: bool) -> List[Alphabet]:
        # this function MUST return the core always as the first element
        modules = [
            Alphabet.CORE_COMPONENT,
            Alphabet.JOINT_HORIZONTAL,
            Alphabet.JOINT_VERTICAL,
            Alphabet.BLOCK,
            #Alphabet.BLOCK1,
            #Alphabet.BLOCK2,
            #Alphabet.BLOCK3,
            #Alphabet.BLOCK4,
        ]
        if allow_vertical_brick:
            modules.append(Alphabet.BLOCK_VERTICAL)
        return modules

    def is_vertical_module(self) -> bool:
        return self is Alphabet.JOINT_VERTICAL \
               or self is Alphabet.BLOCK_VERTICAL

    def is_joint(self) -> bool:
        return self is Alphabet.JOINT_VERTICAL \
               or self is Alphabet.JOINT_HORIZONTAL

    @staticmethod
    def morphology_mounting_commands() -> List[Alphabet]:
        return [
            Alphabet.ADD_RIGHT,
            Alphabet.ADD_FRONT,
            Alphabet.ADD_LEFT,
            Alphabet.ADD_BACK,
        ]

    @staticmethod
    def morphology_moving_commands(use_movement_commands: bool,
                                   use_rotation_commands: bool,
                                   use_movement_stack: bool) -> List[Alphabet]:
        commands = []
        if use_movement_commands:
            commands.append(Alphabet.MOVE_RIGHT)
            commands.append(Alphabet.MOVE_FRONT)
            commands.append(Alphabet.MOVE_LEFT)
            commands.append(Alphabet.MOVE_BACK)
            commands.append(Alphabet.MOVE_NONE)
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
    def controller_changing_commands() -> List[Alphabet]:
        return [
            Alphabet.ADD_EDGE,
            Alphabet.MUTATE_EDGE,
            Alphabet.LOOP,
            Alphabet.MUTATE_AMP,
            Alphabet.MUTATE_PER,
            Alphabet.MUTATE_OFF,
        ]

    @staticmethod
    def controller_moving_commands() -> List[Alphabet]:
        return [
            Alphabet.MOVE_REF_S,
            Alphabet.MOVE_REF_O,
        ]

    @staticmethod
    def wordify(letters: Union[Alphabet, List]
                ) -> Union[(Alphabet, List), List[(Alphabet, List)]]:
        if isinstance(letters, Iterable):
            return [(a, []) for a in letters]
        elif isinstance(letters, Alphabet):
            return (letters, [])
        else:
            raise RuntimeError(f'Cannot wordify element of type {type(letters)}')

    @staticmethod
    def is_block(new_module_type: Alphabet):
        if new_module_type == Alphabet.BLOCK or \
                new_module_type == Alphabet.BLOCK1 or \
                new_module_type == Alphabet.BLOCK2 or \
                new_module_type == Alphabet.BLOCK3 or \
                new_module_type == Alphabet.BLOCK4:
            return True
        return False