from __future__ import absolute_import, unicode_literals
from .celery import app
import asyncio
import jsonpickle
import subprocess
from celery.worker.control import control_command

import os, sys
import random
from pyrevolve.SDF.math import Vector3
from pyrevolve import revolve_bot, parser
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.evolution import fitness
from experiments.examples import only_gazebo
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.custom_logging.logger import logger

from pycelery.converter import args_to_dic, dic_to_args, args_default

# ------------- Collection of tasks ------------------- #

@app.task
async def stupid():
    """Just returns a stupid fitness"""
    return 1.0

@app.task
async def test_worker(settingsDir, i):
    id = i
    loop = asyncio.get_event_loop()

    gazebo_ = asyncio.run_coroutine_threadsafe(run_gazebo.delay(settingsDir, i), loop)

    return True

async def run(loop):

    await asyncio.sleep(5)

    asyncio.get_child_watcher().attach_loop(loop)

    settings = parser.parse_args()

    """ Method 1: The run function is called by the revolve.py, and here we can distribute workers.
    Currently we can start n-1 gazebo instances from here, all on different workers!"""

    settingsDir = args_to_dic(settings)
    gws = []
    grs = []
    for i in range(settings.n_cores - 1):
        gw = await run_gazebo.delay(settingsDir, i)
        gws.append(gw)

    # Testing the last gw.
    for i in range(settings.n_cores - 1):
        gr = await gws[i].get()
        grs.append(gr)

    print(grs[0], grs[1])
    return "Done"





    
    """ METHOD 2: This part works, creates n gazebo instances and connections
    Problem: doesnt use all the workers yet, only one. And letting workers use
    these simulators is hard because then you would have to make connection serializable...
    Possible solution: Not yet found"""

    # gazebo_connections = []
    # gazebo_supervisor = []
    # gazebo_launches = []
    # workers = []
    # for i in range(settings.n_cores):
    #     if settings.simulator_cmd != 'debug':
    #         simulator_supervisor = DynamicSimSupervisor(
    #             world_file=settings.world,
    #             simulator_cmd=settings.simulator_cmd,
    #             simulator_args=["--verbose"],
    #             plugins_dir_path=os.path.join('.', 'build', 'lib'),
    #             models_dir_path=os.path.join('.', 'models'),
    #             simulator_name=f'gazebo_{i}'
    #         )
    #         gazebo_launches.append(simulator_supervisor.launch_simulator(port=settings.port_start+i))
    #         gazebo_supervisor.append(simulator_supervisor)
    #
    # # let there be some time to sync all initial output of the simulator
    # await asyncio.sleep(5)
    #
    # for i, future_launch in enumerate(gazebo_launches):
    #     await future_launch
    #     connection = await World.create(settings, world_address=('127.0.0.1', settings.port_start+i))
    #     gazebo_connections.append(connection)
    #
    # for j, connection in enumerate(gazebo_connections):
    #     gazebo_connections[j] = connection
    #     await connection.pause(False)
    #
    # await asyncio.sleep(1)
    #
    # testje = await test.delay(connection)
    # testjeresult = await testje.get()
    #
    # await asyncio.sleep(20)
    #
    # return results

@app.task
async def run_gazebo(settingsDir, i):
    """Argument i: Core_ID
        Starts a gazebo simulator """

    loop = asyncio.get_event_loop()

    try:
        asyncio.get_child_watcher().attach_loop(loop)

    except:
        print("Attach loop failed.")

    finally:

        # Parse command line / file input arguments
        settings = dic_to_args(settingsDir)

        if settings.simulator_cmd != 'debug':
            simulator_supervisor = DynamicSimSupervisor(
                world_file=settings.world,
                simulator_cmd=settings.simulator_cmd,
                simulator_args=["--verbose"],
                plugins_dir_path=os.path.join('.', 'build', 'lib'),
                models_dir_path=os.path.join('.', 'models'),
                simulator_name=f'gazebo_{i}'
            )
            await simulator_supervisor.launch_simulator(port=settings.port_start+i)
            # let there be some time to sync all initial output of the simulator
            await asyncio.sleep(5)

            # Connect to the simulator and pause
            connection = await World.create(settings, world_address=('127.0.0.1', settings.port_start+i))
            await asyncio.sleep(1)

            print("SIMULATOR "+ str(i) + " STARTED")

    return "SIMULATOR " +str(i) + " ENDED SUCCESFULLY!"
