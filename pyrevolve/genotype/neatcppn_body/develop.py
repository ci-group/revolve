from pyrevolve.genotype.neatcppn_body.config import NeatcppnBodyConfig
from pyrevolve.revolve_bot.revolve_module import CoreModule, Orientation


def neatcppn_body_develop(self, config: NeatcppnBodyConfig) -> CoreModule:
    core_module = CoreModule()
    core_module.id = "core"
    core_module.rgb = [1, 1, 0]
    core_module.orientation = Orientation.NORTH
    return core_module
