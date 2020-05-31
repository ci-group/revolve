import asyncio
import subprocess
import time
import random
from .celery import app
import sys

from pycelery.tasks import shutdown_gazebo, run_gazebo, run_gazebo_and_analyzer, evaluate_robot, start_robot_queue, insert_robot, reset
from pyrevolve.SDF.revolve_bot_sdf_builder import revolve_bot_to_sdf
from pycelery.converter import args_to_dic, dic_to_args, dic_to_pop, pop_to_dic
from pyrevolve.custom_logging.logger import logger
from pyrevolve.SDF.math import Vector3

class CeleryController:
    """
    This class handles requests to celery workers such as starting a process, evaluating a robot or shutting down a process or worker.
    Note that this class also functions as a simulator_queue.

    :param settings: The settings namespace of the experiment.
    """

    def __init__(self, settings, start_workers = True):
        self.settings = settings
        self.settingsDir = args_to_dic(settings)
        self.celery_process = 0
        self.celery_workers = []

        # Start celery
        if start_workers:
            self.start_workers()

    def start_workers(self):
        """
        Starts n_cores celery workers
        """
        # create random worker tags
        x=self.settings.port_start
        worker_string = ""
        for i in range(self.settings.n_cores):
            worker_string += f"worker{x+i} "
            self.celery_workers.append(f"worker{x+i}@sam-Lenovo-ideapad-Y700-15ISK")

        ampqport = random.randint(0,100)

        # this creates a queue for your workers only and cleans that queue.
        app.conf.update(task_default_queue=f"robots{self.settings.port_start}")
        app.control.purge()

        logger.info("Starting a worker at the background using " + str(self.settings.n_cores) + " cores. ")
        self.celery_process = subprocess.Popen(f"celery multi start {worker_string} -Q robots{self.settings.port_start} -A pycelery -P celery_pool_asyncio:TaskPool -l info -c 1", shell=True)

    async def reset_connections(self):
        logger.info("Resetting connection on every worker.")

        futures = []
        for i in range(self.settings.n_cores):
            future = await reset.delay()
            futures.append(future)

        for i in futures:
            await i.get()

    async def reset_celery(self):
        logger.info("Resetting every celery worker and gazebo instance. This will take approximately 25 seconds...")

        await self.shutdown()

        #celery need time to start
        await asyncio.sleep(5)

        self.start_workers()

        # workers need time to start
        await asyncio.sleep(self.settings.n_cores)

        await self.start_gazebo_instances()


    async def shutdown(self):
        """
        A function to call all celery workers and shut them down.
        """

        shutdowns = []
        for i in range(self.settings.n_cores):
            sd = await shutdown_gazebo.delay()
            shutdowns.append(sd)

        for i in range(self.settings.n_cores):
            result = await shutdowns[i].get()

        ## Not sure about this process yet. It might be better to exit these instances in other ways.
        # subprocess.Popen("pkill -9 -f 'celery worker'", shell=True)
        # subprocess.Popen("pkill -9 -f 'gzserver'", shell=True)

        ## Terminate our celery workers.
        #app.control.shutdown(destination=self.celery_workers)

    async def start_gazebo_instances(self):
        """
        This functions starts N_CORES number of gazebo instances.
        Every worker owns one gazebo instance.
        """
        start_cpp = await start_robot_queue.apply_async(("start unique cpp queue",), serializer="json", queue=f"cpp{self.settings.port_start}")

        gws = []
        grs = []
        for i in range(self.settings.n_cores):
            gw = await run_gazebo_and_analyzer.delay(self.settingsDir, i)
            await start_robot_queue.apply_async((f"{self.settings.port_start}",), serializer="json")
            gws.append(gw)

        for j in range(self.settings.n_cores):
            await gws[j].get()

    async def test_robot(self, robot, conf):
        """
        :param robot: robot (individual)
        :param conf: configuration of the experiment
        :return: future which contains fitness and measures.
        """

        # Create a yaml text from robot
        yaml_bot = robot.phenotype.to_yaml()

        future = await evaluate_robot.delay(yaml_bot, conf.fitness_function, self.settingsDir)

        # SDF = revolve_bot_to_sdf(robot.phenotype, Vector3(0, 0, self.settings.z_start), None)
        # #
        # future = await insert_robot.apply_async((str(SDF), 120), serializer="json")

        # return the future
        return future
