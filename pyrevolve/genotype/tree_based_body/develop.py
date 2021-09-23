from dataclasses import dataclass
from typing import Tuple

from .genotype import Genotype
from .config import Config
from pyrevolve.revolve_bot.revolve_module import (
    ActiveHingeModule,
    BrickModule,
    CoreModule,
    RevolveModule,
)
from ..direct_tree.direct_tree_config import DirectTreeGenotypeConfig
from typeguard import typechecked
#from ..direct_tree.direct_tree_genotype import Genotype

@typechecked
def develop(genotype: Genotype, conf) -> CoreModule:
    #DtreeGen = Genotype(conf=DirectTreeGenotypeConfig, robot_id=0)
    #DtreeGen.genotype_impl = genotype.genotype_impl
    bot = genotype.genotype_impl.develop()
    return bot._body

