from __future__ import absolute_import
import logging

logger = logging.getLogger("tol")


def output_console():
    logger.addHandler(logging.StreamHandler())


def log_debug():
    logger.setLevel(logging.DEBUG)
