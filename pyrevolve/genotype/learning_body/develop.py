import logging
import sys
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
from typeguard import typechecked

from .genotype import Genotype
from pyrevolve.custom_logging import logger
from ...revolve_bot import RevolveBot


@typechecked
def develop(genotype: Genotype, config: str) -> CoreModule:
    log = logger.create_logger('experiment', handlers=[ logging.StreamHandler(sys.stdout), ])

    print("wytf")

    # Set debug level to DEBUG
    log.setLevel(logging.DEBUG)
    # load robot file
    path = config
    robot = RevolveBot()
    robot.load_file(path, conf_type='yaml')
    robot.save_file(f'{path}.sdf', conf_type='sdf')
    log.info("SDF saved")

    return robot.body

