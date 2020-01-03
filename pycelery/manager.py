from __future__ import absolute_import, unicode_literals
import asyncio
import jsonpickle
import subprocess
import os, sys
import random
from celery.worker.control import control_command
from pycelery.converter import args_to_dic, dic_to_args, args_default
from pyrevolve import revolve_bot, parser
from pycelery.celerycontroller import CeleryController

async def run(loop):
    """A revolve manager that is tests celery and celery communication."""
    settings = parser.parse_args()

    celerycontroller = CeleryController(settings) # Starting celery

    await asyncio.sleep(5) # Celery needs time

    await celerycontroller.start_gazebo_instances()

    await celerycontroller.distribute_robots(["experiments/examples/yaml/spider.yaml" for i in range(10)])

    fitnesses = await celerycontroller.test_robots() # Start the simulations

    await celerycontroller.shutdown()

    print(fitnesses)
