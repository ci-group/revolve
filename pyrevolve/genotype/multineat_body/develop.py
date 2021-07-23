from dataclasses import dataclass
from queue import Queue
from typing import Any, Optional, Tuple

from pyrevolve.genotype.multineat.genotype import MultineatGenotype
from pyrevolve.genotype.multineat_body.config import MultineatBodyConfig
from pyrevolve.revolve_bot.revolve_module import (
    ActiveHingeModule,
    BrickModule,
    CoreModule,
    RevolveModule,
)


@dataclass
class _Module:
    position: Tuple[int, int, int]
    chain_length: int
    module_reference: CoreModule


def multineat_body_develop(
    genotype: MultineatGenotype, config: MultineatBodyConfig
) -> CoreModule:
    max_parts = 10

    to_explore: Queue[RevolveModule] = Queue()

    core_module = CoreModule()
    core_module.id = "core"
    core_module.rgb = [1, 1, 0]
    core_module.orientation = 0

    to_explore.put(_Module((0, 0, 0), 0, core_module))
    part_count = 1

    while not to_explore.empty():
        module: _Module = to_explore.get()

        child_index_range: range
        if type(module.module_reference) == CoreModule:
            child_index_range = range(0, 4)
        elif type(module.module_reference) == BrickModule:
            child_index_range = range(1, 4)
        elif type(module) == ActiveHingeModule:
            child_index_range = range(1, 2)
        else:  # Should actually never arrive here but just checking module type to be sure
            raise RuntimeError

        for child_index in child_index_range:
            if part_count < max_parts:
                child = _add_child(module, child_index)
                if child != None:
                    to_explore.put(child)
                    part_count += 1

    return core_module


# get module type, orientation
def _get_child_type(
    position: Tuple[int, int, int], chain_length: int
) -> Tuple[Any, int]:
    return (BrickModule, 0)  # TODO


def _add_child(module: _Module, child_index: int) -> Optional[_Module]:
    child_type, orientation = _get_child_type(module.position, module.chain_length)
    if child_type == None:
        return None
    child = child_type()
    child.id = module.module_reference.id + "_" + str(child_index)
    child.orientation = orientation
    if child_type == BrickModule:
        child.rgb = [1, 0, 0]
    elif child_type == ActiveHingeModule:
        child.rgb = [0, 1, 0]
    else:
        # Should actually never arrive here but just checking module type to be sure
        raise RuntimeError

    module.module_reference.children[child_index] = child
    return _Module((0, 0, 0), 0, child)  # TODO

    # revolve_bot -> update_subtrate throws on collision (raise for intersection True)
