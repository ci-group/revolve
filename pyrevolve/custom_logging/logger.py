from __future__ import absolute_import

import logging
import sys


def create_logger(name='revolve', level=logging.DEBUG, handler=None):
    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    _console_handler = logging.StreamHandler(sys.stdout) if handler is None else handler
    _console_handler.setLevel(level)
    _revolve_formatter = logging.Formatter('[%(asctime)s %(name)10s] %(levelname)-8s %(message)s')
    _console_handler.setFormatter(_revolve_formatter)
    _logger.addHandler(_console_handler)
    return _logger

logging.WARNING
logging.CRITICAL

# General logger to standard output
logger = create_logger(
    name='revolve',
    level=logging.DEBUG,
    handler=logging.StreamHandler(sys.stdout)
)

# Genotype logger for logging mutation and crossover details to a file
genotype_logger = create_logger(
    name='genotype',
    level=logging.INFO,
    handler=logging.FileHandler('./genotype.log', mode='w')
)
