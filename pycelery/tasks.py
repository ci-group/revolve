from __future__ import absolute_import, unicode_literals
from .celery import app
import asyncio
import importlib
import os

from pyrevolve import revolve_bot
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.custom_logging.logger import logger
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import measures
from pycelery.converter import args_to_dic, dic_to_args, args_default, pop_to_dic, dic_to_pop, measurements_to_dict
from celery.app.control import Control

"""The unique variables per worker (!!!NONE OF THEM HAVE TO BE SET IN ADVANCE!!!)
    :variable connection: connection with a gazebo instance.
    :variable settings: The settings of the experiment.
    :variable simulator_supervisor: The supervisor linked with @connection.
    :variable robot_queue: a asyncio queue to store the robots locally
    :variable fitness_function: a function which the simulator_worker will use as fitness."""

connection = None
settings = None
simulator_supervisor = None
# robot_queue = asyncio.Queue(maxsize=4)
fitness_function = None

# ------------- Collection of tasks ------------------- #
@app.task
async def run_gazebo(settingsDir, i):
    """
    Starts a gazebo simulator with name gazebo_ID

    :param settingsDir: a dictionary of the settings.
    :param i: an integer representing the worker ID or number.
    """

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

            # asyncio.ensure_future(simulator_worker(settingsDir, i))

    return True

@app.task(queue = 'robots')
async def put_in_queue(robot, fitnessName):
    """
    A celery task that puts the robot in a workers queue.
    CURRENTLY NOT IN USE

    :param robot: a yaml object which represents a revolve bot.
    :param fitnessName: a string of the fitness_function used.
    """
    global robot_queue
    global fitness_function

    # Set global fitness_function
    if fitness_function == None:
        function_string = 'pyrevolve.evolution.fitness.' + fitnessName
        mod_name, func_name = function_string.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        fitness_function = getattr(mod, fitnessName)

    future = asyncio.Future()

    robot_queue.put_nowait((robot, future))
    if robot_queue.qsize() > 2:
        app.control.cancel_consumer(queue="robots")

    result = await future
    return result

@app.task(queue="robots")
async def evaluate_robot(yaml_object, fitnessName, settingsDir):
    global connection
    global fitness_function

    # Set global fitness_function
    if fitness_function == None:
        function_string = 'pyrevolve.evolution.fitness.' + fitnessName
        mod_name, func_name = function_string.rsplit('.',1)
        mod = importlib.import_module(mod_name)
        fitness_function = getattr(mod, fitnessName)

    settings = dic_to_args(settingsDir)
    max_age = settings.evaluation_time

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

    BehaviouralMeasurementsDic = measurements_to_dict(robot_manager, robot)
    return (robot_fitness, BehaviouralMeasurementsDic)

async def simulator_worker(settingsDir, i):
    """
    This function represents the worker and is activated by run_gazebo above.
    It will evaluate robots that are in the robot_queue.

    :param settingsDir: A dictionary of the settings.
    :param i: an integer representing the worker ID or number.
    """
    global connection
    global robot_queue
    global fitness_function

    settings = dic_to_args(settingsDir)
    max_age = settings.evaluation_time
    running = False

    while True:
        # Load the robot
        logger.info(f"Simulator {i} waiting for next robot")
        logger.info(f"Queuesize is {robot_queue.qsize()}")
        (yaml_object, future) = await robot_queue.get()
        if robot_queue.qsize() < 2:
            app.control.add_consumer(queue = "robots")

        running = True

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

        BehaviouralMeasurementsDic = measurements_to_dict(robot_manager, robot)
        future.set_result((robot_fitness, BehaviouralMeasurementsDic))

@app.task
async def shutdown_gazebo():
    """
    Shutsdown the local running gazebo if there is one.
    """

    global simulator_supervisor
    global connection
    try:
        await connection.disconnect()
        await asyncio.wait_for(simulator_supervisor.stop(), timeout=2)
    except:
        print("TimeoutError: timeout error when closing gazebo instance.")
    finally:
        return True
