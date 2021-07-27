from dataclasses import dataclass
from queue import Queue
from typing import Any, Optional, Tuple

import multineat
from pyrevolve.genotype.cppnneat.genotype import CppnneatGenotype
from pyrevolve.genotype.cppnneat_body.config import CppnneatBodyConfig
from pyrevolve.revolve_bot.revolve_module import (ActiveHingeModule,
                                                  BrickModule, CoreModule,
                                                  RevolveModule)

"""
Not using a library for vector because it's super simple with int and I don't feel like using numpy at this moment
"""


@dataclass
class _Module:
    position: Tuple[int, int, int]
    forward: Tuple[int, int, int]
    up: Tuple[int, int, int]
    chain_length: int
    module_reference: CoreModule


def cppnneat_body_develop(
    genotype: CppnneatGenotype, config: CppnneatBodyConfig
) -> CoreModule:
    max_parts = 10

    body_net = multineat.NeuralNetwork()
    genotype.multineat_genome.BuildPhenotype(body_net)

    to_explore: Queue[RevolveModule] = Queue()

    core_module = CoreModule()
    core_module.id = "core"
    core_module.rgb = [1, 1, 0]
    core_module.orientation = 1

    to_explore.put(
        _Module((0, 0, 0), (0, -1, 0), (0, 0, 1), 0, core_module)
    )  # forward is always slot 1
    part_count = 1

    while not to_explore.empty():
        module: _Module = to_explore.get()

        child_index_range: range
        if type(module.module_reference) == CoreModule:
            child_index_range = range(0, 4)
        elif type(module.module_reference) == BrickModule:
            child_index_range = range(1, 4)
        elif type(module.module_reference) == ActiveHingeModule:
            child_index_range = range(1, 2)
        else:  # Should actually never arrive here but just checking module type to be sure
            raise RuntimeError

        for child_index in child_index_range:
            if part_count < max_parts:
                child = _add_child(body_net, module, child_index)
                if child != None:
                    to_explore.put(child)
                    part_count += 1

    return core_module


# get module type, orientation
def _evaluate_cppg(
    body_net: multineat.NeuralNetwork,
    position: Tuple[int, int, int],
    chain_length: int,
) -> Tuple[Any, int]:
    body_net.Input(
        [1.0, position[0], position[1], position[2], chain_length]
    )  # 1.0 is the bias input
    body_net.Activate()
    outputs = body_net.Output()

    # get module type from output probabilities
    type_probs = [outputs[0], outputs[1], outputs[2]]
    types = [None, BrickModule, ActiveHingeModule]
    module_type = types[type_probs.index(min(type_probs))]

    # get rotation from output probabilities
    rotation_probs = [outputs[3], outputs[4]]
    rotation = rotation_probs.index(min(rotation_probs))

    return (module_type, rotation)


def _add_child(
    body_net: multineat.NeuralNetwork, module: _Module, child_index: int
) -> Optional[_Module]:
    forward = _get_new_forward(module.forward, module.up, child_index)
    position = _add(module.position, forward)
    chain_length = module.chain_length + 1

    child_type, orientation = _evaluate_cppg(body_net, position, chain_length)
    if child_type == None:
        return None

    child = child_type()
    module.module_reference.children[child_index] = child
    child.id = module.module_reference.id + "_" + str(child_index)
    child.orientation = orientation * 90

    # coloring
    if child_type == BrickModule:
        child.rgb = [1, 0, 0]
    elif child_type == ActiveHingeModule:
        child.rgb = [0, 1, 0]
    else:  # Should actually never arrive here but just checking module type to be sure
        raise RuntimeError

    up = _get_new_up(module.up, forward, orientation)
    return _Module(
        position,
        forward,
        up,
        chain_length,
        child,
    )

    # TODO check for self collision?
    # revolve_bot -> update_subtrate throws on collision (raise for intersection True)


def _get_new_forward(
    parent_forward: Tuple[int, int, int], parent_up: Tuple[int, int, int], slot: int
) -> Tuple[int, int, int]:
    rotation: int
    if slot == 0:
        rotation = 2
    elif slot == 1:
        rotation = 0
    elif slot == 2:
        rotation = 3
    else:
        rotation = 1

    return _rotate(parent_forward, parent_up, rotation)


def _get_new_up(
    parent_up: Tuple[int, int, int], new_forward: Tuple[int, int, int], orientation: int
) -> Tuple[int, int, int]:
    return _rotate(parent_up, new_forward, orientation)


def _add(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return tuple(map(sum, zip(a, b)))


def _timesscalar(a: Tuple[int, int, int], scalar: int) -> Tuple[int, int, int]:
    return (a[0] * scalar, a[1] * scalar, a[2] * scalar)


def _cross(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> Tuple[int, int, int]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: Tuple[int, int, int], b: Tuple[int, int, int]) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


# rotates a around b. angle from [0,1,2,3]. 90 degrees each
def _rotate(
    a: Tuple[int, int, int], b: Tuple[int, int, int], angle: int
) -> Tuple[int, int, int]:
    cosangle: int
    sinangle: int
    if angle == 0:
        cosangle = 1
        sinangle = 0
    elif angle == 1:
        cosangle = 0
        sinangle = 1
    elif angle == 2:
        cosangle = -1
        sinangle = 0
    else:
        cosangle = 0
        sinangle = -1

    return _add(
        _add(_timesscalar(a, cosangle), _timesscalar(_cross(b, a), sinangle)),
        _timesscalar(b, _dot(b, a) * (1 - cosangle)),
    )
