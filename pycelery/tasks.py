from __future__ import absolute_import, unicode_literals
from .celery import app
import asyncio
import importlib
import os

from celery.exceptions import SoftTimeLimitExceeded
from pyrevolve import revolve_bot
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.gazebo.analyze import BodyAnalyzer
from pyrevolve.util.supervisor.supervisor_collision import CollisionSimSupervisor
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
fitness_function = None
analyzer_connection = None
analyzer_supervisor = None
id = None

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


    return True

@app.task
async def run_gazebo_and_analyzer(settingsDir, i):
    """
    Starts a gazebo simulator with name gazebo_ID

    :param settingsDir: a dictionary of the settings.
    :param i: an integer representing the worker ID or number.
    """

    global settings
    global connection
    global analyzer_connection
    global analyzer_supervisor
    global simulator_supervisor
    global id

    id = i

    loop = asyncio.get_event_loop()

    try:
        asyncio.get_child_watcher().attach_loop(loop)

    except:
        print("Attach loop failed.")

    finally:

        # Parse command line / file input arguments

        settings = dic_to_args(settingsDir)

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

        await asyncio.sleep(2)

        analyzer_supervisor = CollisionSimSupervisor(
            world_file=os.path.join('tools', 'analyzer', 'analyzer-world.world'),
            simulator_cmd="gzserver",
            simulator_args=["--verbose"],
            plugins_dir_path=os.path.join('.', 'build', 'lib'),
            models_dir_path=os.path.join('.', 'models'),
            simulator_name=f'analyzer_{i}'
        )

        await analyzer_supervisor.launch_simulator(port=settings.port_start+i+settings.n_cores)

        await asyncio.sleep(5)

        analyzer_connection = await BodyAnalyzer.create('127.0.0.1', settings.port_start+i+settings.n_cores)

        await asyncio.sleep(2)

    return True

async def _restart_simulator(settings, connection_, supervisor_, simulator_type):
    global id
    global analyzer_connection
    global connection

    address = '127.0.0.1'
    port = settings.port_start+id+settings.n_cores

    logger.error("Restarting simulator")
    logger.error("Restarting simulator... disconnecting")
    try:
        await asyncio.wait_for(connection_.disconnect(), 10)
    except asyncio.TimeoutError:
        pass

    logger.error("Restarting simulator... restarting")
    await supervisor_.relaunch(10, adress=adress, port=port)

    await asyncio.sleep(5)

    logger.debug("Restarting simulator done... connecting")

    if simulator_type == "analzer":
        analyzer_connection = await BodyAnalyzer.create(adress, port)
    else:
        connection = await World.create(settings, world_address=('127.0.0.1', settings.port_start+id))

    logger.debug("Restarting simulator done... connection done")

@app.task(queue="robots", time_limit = 120)
async def evaluate_robot(yaml_object, fitnessName, settingsDir):
    global connection
    global analyzer_connection
    global simulator_supervisor
    global analyzer_supervisor
    global fitness_function

    try:

        EVALUATION_TIMEOUT = 30

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

        if analyzer_connection:
            try:
                collisions, _bounding_box = await asyncio.wait_for(analyzer_connection.analyze_robot(robot), timeout=EVALUATION_TIMEOUT)
            except asyncio.TimeoutError:
                await _restart_simulator(settings, analyzer_connection, analyzer_supervisor, "analyzer")
                return (None, None)

            if collisions > 0:
                logger.info(f"discarding robot {robot.id} because there are {collisions} self collisions")
                return (None, None)

        # Simulate robot
        robot_manager = await connection.insert_robot(robot, Vector3(0, 0, settings.z_start), max_age)

        while not robot_manager.dead:
            await asyncio.sleep(0.1)

        ### WITHOUT THE FLOAT(), CELERY WILL GIVE AN ERROR ###
        robot_fitness = float(fitness_function(robot_manager, robot))

        # Remove robot, reset, and let other robot run.
        connection.unregister_robot(robot_manager)
        await connection.reset(rall=True, time_only=True, model_only=False)

        BehaviouralMeasurementsDic = measurements_to_dict(robot_manager, robot)
        return (robot_fitness, BehaviouralMeasurementsDic)

    except SoftTimeLimitExceeded:
        _restart_simulator(settings, connection, simulator_supervisor, "simulator")
        return (None, None)

@app.task(queue="robots", time_limit = 120)
async def evaluate_robot_test(yaml_object, fitnessName, settingsDir):

    try:

        EVALUATION_TIMEOUT = 30

        settings = dic_to_args(settingsDir)
        max_age = settings.evaluation_time

        robot = revolve_bot.RevolveBot()
        robot.load_yaml(yaml_object)
        robot.update_substrate()
        robot.measure_phenotype()

        # Simulate robot
        robot_manager = await insert_robot.delay(str(robot.phenotype.id))

        robot_fitness = await robot_manager.get()

        return (robot_fitness, None)

    except SoftTimeLimitExceeded:
        _restart_simulator(settings, connection, simulator_supervisor, "simulator")
        return (None, None)

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

@app.task(queue="celery")
async def insert_robot(name):
    print("This will be handled by c++ part in worldcontroller.")
