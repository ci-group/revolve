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
from ..plasticoding.plasticoding import Plasticoding,PlasticodingConfig
from typeguard import typechecked

from .genotype import Genotype

@typechecked
def develop(genotype: Genotype, config: Config) -> CoreModule:
    plasticoding = Plasticoding(conf=config.plasticoding_config, robot_id=0)
    plasticoding.grammar = genotype.genotype_impl
    bot = plasticoding.develop('plane')
    return bot._body

