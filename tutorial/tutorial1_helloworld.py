#!/usr/bin/env python3
import os
import sys
from pyrevolve.custom_logging.logger import logger


# ./revolve.py --simulator-cmd=gazebo --manager tutorial/tutorial1_helloworld.py
async def run():
    logger.info('Hello World!')