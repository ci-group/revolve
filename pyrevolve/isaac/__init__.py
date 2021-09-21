import logging
import sys
from pyrevolve.custom_logging.logger import create_logger
isaac_logger: logging.Logger = create_logger(
    name='isaac',
    level=logging.DEBUG,
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler('./revolve_isaac.log', mode='a')]
)

from .CPG_controller import CPG
