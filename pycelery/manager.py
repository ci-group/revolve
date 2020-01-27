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
    """A revolve manager that is using celery for task execution."""
    settings = parser.parse_args()

    celerycontroller = CeleryController(settings) # Starting celery

    await asyncio.sleep(5) # Celery needs time

    await celerycontroller.start_gazebo_instances()

    # Make 10 robots using revolve bot.
    population = []
    robot_file_path = "experiments/examples/yaml/spider.yaml"

    for i in range(10):
        robot = revolve_bot.RevolveBot()
        robot.load_file(robot_file_path)
        robot.update_substrate()

        population.append(robot)

    # Make a list of yaml strings from population.
    yaml_population = [robot.to_yaml() for robot in population]

    # send the strings to celery
    # await celerycontroller.distribute_robots(["experiments/examples/yaml/spider.yaml" for i in range(10)])

    # fitnesses = await celerycontroller.test_robots() # Start the simulations

    await celerycontroller.shutdown()

    # print(fitnesses)
