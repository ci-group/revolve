from __future__ import absolute_import

import logging
import sys

# General logger to standard output
logger = logging.getLogger('revolve')
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
revolve_formatter = logging.Formatter('[%(name)s] %(levelname)s  %(message)s')
console_handler.setFormatter(revolve_formatter)
logger.addHandler(console_handler)

# Genotype logger for logging mutation and crossover details to a file
genotype_logger = logging.getLogger('genotype')
genotype_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('./genotype.log', mode='w')
file_handler.setLevel(logging.INFO)
genotype_formatter = logging.Formatter('%(message)s')
file_handler.setFormatter(genotype_formatter)
genotype_logger.addHandler(file_handler)