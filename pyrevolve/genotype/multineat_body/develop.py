from queue import Queue

from pyrevolve.genotype.multineat.genotype import MultineatGenotype
from pyrevolve.genotype.multineat_body.config import MultineatBodyConfig
from pyrevolve.revolve_bot.revolve_module import (
    ActiveHingeModule,
    BrickModule,
    CoreModule,
    RevolveModule,
)


def multineat_body_develop(
    genotype: MultineatGenotype, config: MultineatBodyConfig
) -> CoreModule:
    max_parts = 10

    to_explore: Queue[RevolveModule] = Queue()

    core_module = CoreModule()
    core_module.id = "core"
    core_module.rgb = [1, 1, 0]
    core_module.orientation = 0

    to_explore.put(core_module)
    part_count = 1

    while not to_explore.empty():
        module: RevolveModule = to_explore.get()
        if type(module) == CoreModule:
            for child_index in range(0, 4):
                if part_count < max_parts:
                    child = BrickModule()
                    child.id = str(part_count)
                    child.rgb = [1, 0, 0]
                    child.orientation = 0
                    module.children[child_index] = child

                    to_explore.put(child)
                    part_count += 1
        elif type(module) == BrickModule:
            for child_index in range(1, 4):
                if part_count < max_parts:
                    child = BrickModule()
                    child.id = str(part_count)
                    child.rgb = [1, 0, 0]
                    child.orientation = 0
                    module.children[child_index] = child

                    to_explore.put(child)
                    part_count += 1
        elif type(module) == ActiveHingeModule:
            pass
        else:
            # Should actually never arrive here but just checking module type to be sure
            raise RuntimeError

    return core_module
