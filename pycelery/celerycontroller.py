import asyncio
import subprocess
import time
from pycelery.tasks import shutdown_gazebo, run_gazebo, put_in_queue, test_robot
from pycelery.converter import args_to_dic, dic_to_args

class CeleryController:
    """This class handles requests to celery workers such as starting a process,
    shutting down a process or worker. """

    def __init__(self, settings):
        self.settings = settings
        self.settingsDir = args_to_dic(settings)

        # Start celery
        self.start_workers()

    def start_workers(self):
        """Starts n_cores celery workers """

        print("Starting a worker at the background using " + str(self.settings.n_cores) + " cores.")
        subprocess.Popen("celery multi restart "+str(self.settings.n_cores)+" -A pycelery -P celery_pool_asyncio:TaskPool --loglevel=info -c 0", shell=True)

    async def shutdown(self):
        """A function to call all workers and shut them down."""
        
        shutdowns = []
        for i in range(self.settings.n_cores):
            sd = await shutdown_gazebo.delay()
            shutdowns.append(sd)

        for i in range(self.settings.n_cores):
            await shutdowns[i].get()

        subprocess.Popen("pkill -9 -f 'celery worker'", shell=True)


    async def start_gazebo_instances(self):
        """ This functions starts N_CORES number of gazebo instances.
        For every worker one."""

        gws = []
        grs = []
        for i in range(self.settings.n_cores):
            gw = await run_gazebo.delay(self.settingsDir, i)
            gws.append(gw)

        # Testing the last gw.
        for j in range(self.settings.n_cores):
            gr = await gws[j].get()
            grs.append(gr)

        return grs

    async def distribute_robots(self, robots):
        """A function that distributes a list of robots (string locations)
        to different workers.
        param: List of robots string locations
        """
        population = []
        for k in robots:
            robot = await put_in_queue.delay(k)
            population.append(robot)

        for l in population:
            fitness = await l.get()

    async def test_robots(self):
        running_workers = []
        for i in range(self.settings.n_cores):
            start = await test_robot.delay(self.settingsDir)
            running_workers.append(start)

        fitnesses = []
        for i in range(self.settings.n_cores):
            result = await running_workers[i].get()
            fitnesses.append(result)

        return fitnesses
