import random
import math
import queue
import uuid
from typing import Tuple, List, Optional, Type

from pyrevolve.genotype.direct_tree.direct_tree_utils import recursive_iterate_modules
from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeGenotypeConfig
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.revolve_module import RevolveModule, CoreModule, BrickModule, ActiveHingeModule, Orientation


possible_orientation: List[float] = [0, 90, 180, 270]

module_short_name_conversion = {
    BrickModule: 'B',
    ActiveHingeModule: 'J',
    CoreModule: 'C',
}

possible_children: List[Optional[Type[RevolveModule]]] = [
    None,
    BrickModule,
    ActiveHingeModule
]


def generate_tree(core: CoreModule,
                  max_parts: int,
                  n_parts_mu: float,
                  n_parts_sigma: float,
                  config: DirectTreeGenotypeConfig) \
        -> CoreModule:
    """
    Generate
    :param core: Core module of the tree
    :param max_parts: max number of blocks to generate
    :param n_parts_mu: target size of the tree (gauss mu)
    :param n_parts_sigma: variation of the target size of the tree (gauss sigma)
    :param config: genotype configuration
    :return: the updated core
    """
    robot = RevolveBot()
    robot._body = core

    count_parts = 1
    _max_parts: int = math.floor(
        random.gauss(n_parts_mu, n_parts_sigma) + 0.5
    )
    max_parts = min(max_parts, _max_parts)


    core_color: Tuple[float, float, float] = (
        random.uniform(0, 1),
        random.uniform(0, 1),
        random.uniform(0, 1)
    )

    core.id = 'C'
    core.rgb = core_color

    # Breadth First Search
    # difference by discovered and not labeled is done by doing the update_substrate.
    # it's a slow solution, but it reuses code that we already now as working.

    slot_queue = queue.Queue()  # infinite FIFO queue

    def append_new_empty_slots(module: RevolveModule):
        for slot_i, _child in module.iter_children():
            # slot is (i, null_ref)
            slot_queue.put((module, slot_i))

    append_new_empty_slots(core)

    possible_children_probs: List[float] = [
        config.init.prob_no_child,
        config.init.prob_child_block,
        config.init.prob_child_active_joint,
    ]

    while count_parts <= max_parts and not slot_queue.empty():
        # position and reference
        parent, chosen_slot \
            = slot_queue.get_nowait()  # type: (RevolveModule, int)

        new_child_module: RevolveModule = generate_new_module(parent, chosen_slot, possible_children_probs, config)
        if new_child_module is None:
            continue

        try:
            # add it to parent
            parent.children[chosen_slot] = new_child_module
            robot.update_substrate(raise_for_intersections=True)
        except RevolveBot.ItersectionCollisionException:
            # could not add module, the slot was already occupied
            # (meaning this position was already occupied by a previous node)
            parent.children[chosen_slot] = None
            continue

        # add new module's slots to the queue
        append_new_empty_slots(new_child_module)
        count_parts += 1

    module_ids = set()
    for _, _, module, _ in recursive_iterate_modules(core, include_none_child=False):
        assert module.id not in module_ids
        module_ids.add(module.id)

    return core


def generate_new_module(parent: RevolveModule,
                        parent_free_slot: int,
                        possible_children_probs: List[float],
                        config: DirectTreeGenotypeConfig) \
        -> Optional[RevolveModule]:
    """
    Generates new random block
    :param parent: only for new module id
    :param parent_free_slot: only for new module id
    :param possible_children_probs: probabilites on how to select the new module, list of 3 floats.
    :param config: genotype configuration
    :return: returns new module, or None if the probability to not select any new module was extracted
    """
    module_color: Tuple[float, float, float] = (
        random.uniform(0, 1),
        random.uniform(0, 1),
        random.uniform(0, 1)
    )

    new_child_module_class = random.choices(possible_children,
                                            weights=possible_children_probs,
                                            k=1)[0]
    if new_child_module_class is None:
        # randomly chose to close this slot
        return None

    new_child_module: RevolveModule = new_child_module_class()

    # random rotation
    new_child_module.orientation = random.choice(possible_orientation)

    # generate module ID
    short_mod_type = module_short_name_conversion[new_child_module_class]
    # new_child_module.id = f'{parent.id}{Orientation(parent_free_slot).short_repr()}_{short_mod_type}'
    new_child_module.id = str(uuid.uuid1())
    new_child_module.rgb = module_color

    # if is active, add oscillator parameters
    if isinstance(new_child_module, ActiveHingeModule):
        new_child_module.oscillator_period = random.uniform(0, config.max_oscillation)
        # makes no sense to shift it more than the max oscillation period
        new_child_module.oscillator_phase = random.uniform(0, config.max_oscillation)
        # output is capped between (0,1) excluded
        new_child_module.oscillator_amplitude = random.uniform(0, 1)

    return new_child_module
