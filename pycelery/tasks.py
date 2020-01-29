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
from celery.signals import celeryd_init, worker_process_init
from pycelery.converter import args_to_dic, dic_to_args, args_default, pop_to_dic, dic_to_pop

# ------------- Collection of tasks ------------------- #
connection = None
settings = None
simulator_supervisor = None
robot_queue = asyncio.Queue()

@app.task
async def run_gazebo(settingsDir, i):
    """Argument i: Core_ID
        Starts a gazebo simulator with name gazebo_ID """
    global settings
    global connection
    global simulator_supervisor

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


    return "SIMULATOR "+ str(i) + " STARTED"

@app.task
async def put_in_queue(yaml_object):
    """Puts a robot in the queue of the local worker responding to this task"""
    global robot_queue
    robot_queue.put_nowait(yaml_object)

@app.task
async def evaluate_robot(yaml_object, settingsDir):
    global connection

    settings = dic_to_args(settingsDir)
    # conf = dic_to_pop(populationDir)

    max_age = settings.evaluation_time

    # Load the robot
    robot = revolve_bot.RevolveBot()
    robot.load_yaml(yaml_object)
    robot.update_substrate()

    # Simulate robot
    robot_manager = await connection.insert_robot(robot, Vector3(0, 0, settings.z_start), max_age)

    while not robot_manager.dead:
        await asyncio.sleep(1.0/2)

    # Calc Fitness
    robot_fitness = fitness.displacement(robot_manager, robot)

    # Remove robot and reset.
    connection.unregister_robot(robot_manager)
    await connection.reset(rall=True, time_only=True, model_only=False)

    return robot_fitness, None

@app.task
async def shutdown_gazebo():
    """Shutsdown the local running gazebo if there is one.
    Always seems so give a timeouterror when stopping gazebo."""

    global simulator_supervisor
    global connection
    try:
        await connection.disconnect()
        await asyncio.wait_for(simulator_supervisor.stop(), timeout=2)
    except:
        print("TimeoutError: timeout error when closing gazebo instance.")
    finally:
        return True
