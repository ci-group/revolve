from __future__ import absolute_import, unicode_literals
import asyncio
import jsonpickle
import subprocess
import os, sys
import random
from celery.worker.control import control_command
from pycelery.converter import args_to_dic, dic_to_args, args_default
from pycelery.tasks import run_gazebo, test_robots, shutdown_gazebo, shutdown, put_in_queue
from pyrevolve import revolve_bot, parser

async def run(loop):
    await asyncio.sleep(5)

    asyncio.get_child_watcher().attach_loop(loop)

    settings = parser.parse_args()

    settingsDir = args_to_dic(settings)
    gws = []
    grs = []
    for i in range(settings.n_cores):
        gw = await run_gazebo.delay(settingsDir, i)
        gws.append(gw)

    # Testing the last gw.
    for j in range(settings.n_cores):
        gr = await gws[j].get()
        grs.append(gr)


    population = []
    for k in range(10):
        robot = await put_in_queue.delay("experiments/examples/yaml/spider.yaml")
        population.append(robot)

    for l in population:
        fitness = await l.get()

    running_workers = []
    for i in range(settings.n_cores):
        start = await test_robots.delay(settingsDir)
        running_workers.append(start)

    fitnesses = []
    for i in range(settings.n_cores):
        result = await running_workers[i].get()
        fitnesses.append(result)
    # shutdown workers

    await shutdown(settings.n_cores)

    print(fitnesses)
    return fitnesses
