from __future__ import absolute_import, unicode_literals
from .celery import app
import asyncio
import jsonpickle
import subprocess
import importlib
import os, sys
import random

from pyrevolve.evolution.individual import Individual
from pyrevolve import revolve_bot, parser
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.evolution import fitness
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
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import measures
from pycelery.converter import args_to_dic, dic_to_args, args_default, pop_to_dic, dic_to_pop, measurements_to_dict

"""The unique variables per worker
    :variable connection: connection with a gazebo instance.
    :variable settings: The settings of the experiment.
    :variable simulator_supervisor: The supervisor linked with @connection.
    :variable running: a boolean telling if a robot is being ran.
    :variable waitinglist: A list of yaml_objects which need to be evaluated."""

connection = None
settings = None
simulator_supervisor = None
running = False
robot_queue = asyncio.Queue()

# ------------- Collection of tasks ------------------- #
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
async def evaluate_robot(yaml_object, settingsDir, fitnessName):
    global connection
    global running
    global waitingList

    # Evaluating the fitness function
    function_string = 'pyrevolve.evolution.fitness.' + fitnessName
    mod_name, func_name = function_string.rsplit('.',1)
    mod = importlib.import_module(mod_name)
    fitness_function = getattr(mod, fitnessName)

    # Make sure to wait for a running process.
    waitingList.append(yaml_object)
    while True:
        if running:
            await asyncio.sleep(1.0)
        elif waitingList[0] == yaml_object: # if it is my turn
            running = True
            break

    settings = dic_to_args(settingsDir)

    max_age = settings.evaluation_time

    # Load the robot
    robot = revolve_bot.RevolveBot()
    robot.load_yaml(yaml_object)
    robot.update_substrate()
    robot.measure_phenotype()

    # Simulate robot
    robot_manager = await connection.insert_robot(robot, Vector3(0, 0, settings.z_start), max_age)

    while not robot_manager.dead:
        await asyncio.sleep(1.0/2)

    ### WITHOUT THE FLOAT(), CELERY WILL GIVE AN ERROR ###
    robot_fitness = float(fitness_function(robot_manager, robot))

    # Remove robot, reset, and let other robot run.
    connection.unregister_robot(robot_manager)
    await connection.reset(rall=True, time_only=True, model_only=False)
    running = False
    waitingList.remove(yaml_object)

    BehaviouralMeasurementsDic = measurements_to_dict(robot_manager, robot)
    return robot_fitness, BehaviouralMeasurementsDic

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
