import random
import math
import queue

from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeGenotypeConfig
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.revolve_module import RevolveModule, CoreModule, BrickModule, ActiveHingeModule, Orientation


def generate_tree(core: CoreModule, config: DirectTreeGenotypeConfig) -> CoreModule:
    assert isinstance(core, CoreModule)
    robot = RevolveBot()
    robot._body = core

    count_parts = 1
    max_parts: int = math.floor(
        random.gauss(config.init.n_parts_mu, config.init.n_parts_sigma) + 0.5
    )
    max_parts = min(config.max_parts, max_parts)

    possible_children = [
        None,
        BrickModule,
        ActiveHingeModule
    ]
    possible_children_probs = [
        config.init.prob_no_child,
        config.init.prob_child_block,
        config.init.prob_child_active_joint,
    ]
    possible_orientation = [0, 90, 180, 270]

    module_short_name_conversion = {
        BrickModule: 'B',
        ActiveHingeModule: 'J',
        CoreModule: 'C',
    }

    core.id = 'C'

    robot_color = (
        random.uniform(0, 1),
        random.uniform(0, 1),
        random.uniform(0, 1)
    )
    core.rgb = robot_color

    # Breadth First Search
    # difference by discovered and not labeled is done by doing the update_substrate.
    # it's a slow solution, but it reuses code that we already now as working.

    slot_queue = queue.Queue()  # infinite FIFO queue

    def append_new_empty_slots(module: RevolveModule):
        for slot_i, _child in module.iter_children():
            # slot is (i, null_ref)
            slot_queue.put((module, slot_i))

    append_new_empty_slots(core)

    while count_parts <= max_parts and not slot_queue.empty():
        # position and reference
        parent, chosen_slot \
            = slot_queue.get_nowait()  # type: (RevolveModule, int)

        new_child_module_class = random.choices(possible_children,
                                                weights=possible_children_probs,
                                                k=1)[0]
        if new_child_module_class is None:
            # randomly chose to close this slot
            continue

        new_child_module: RevolveModule = new_child_module_class()

        # random rotation
        new_child_module.orientation = random.choice(possible_orientation)

        try:
            # add it to parent
            parent.children[chosen_slot] = new_child_module
            robot.update_substrate(raise_for_intersections=True)
        except RevolveBot.ItersectionCollisionException:
            # could not add module, the slot was already occupied
            # (meaning this position was already occupied by a previous node)
            parent.children[chosen_slot] = None
            continue

        # TODO generate ID
        short_mod_type = module_short_name_conversion[new_child_module_class]
        new_child_module.id = f'{parent.id}{Orientation(chosen_slot).short_repr()}_{short_mod_type}'
        new_child_module.rgb = robot_color

        # add new module's slots to the queue
        append_new_empty_slots(new_child_module)

        # if is active, add oscillator parameters
        if isinstance(new_child_module, ActiveHingeModule):
            new_child_module.oscillator_period = random.uniform(0, config.max_oscillation)
            # makes no sense to shift it more than the max oscillation period
            new_child_module.oscillator_phase = random.uniform(0, config.max_oscillation)
            # output is capped between (0,1) excluded
            new_child_module.oscillator_amplitude = random.uniform(0, 1)

        count_parts += 1

    return core
