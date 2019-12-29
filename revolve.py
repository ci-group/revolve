#!/usr/bin/env python3
import os
import sys
import asyncio
import importlib
import subprocess
from subprocess import *

from pyrevolve.data_analisys.visualize_robot import test_robot_run
from pyrevolve.data_analisys.check_robot_collision import test_collision_robot
from pyrevolve import parser
from experiments.examples import only_gazebo
from pycelery import tasks

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def run(loop, arguments):
    n_cores = 1

    if arguments.n_cores is not None:
        n_cores = arguments.n_cores

    if arguments.celery:
        print("Starting a worker at the background using " + str(n_cores) + " cores.")
        subprocess.Popen("celery multi restart "+str(n_cores)+" -A pycelery -P celery_pool_asyncio:TaskPool --loglevel=info -c 0", shell=True) #-P celery_pool_asyncio:TaskPool --scheduler celery_pool_asyncio:PersistentScheduler

    if arguments.test_robot is not None:
        return loop.run_until_complete(test_robot_run(arguments.test_robot))

    if arguments.test_robot_collision is not None:
        return loop.run_until_complete(test_collision_robot(arguments.test_robot_collision))

    if arguments.manager is not None:
        # this split will give errors on windows
        manager_lib = os.path.splitext(arguments.manager)[0]
        manager_lib = '.'.join(manager_lib.split('/'))
        manager = importlib.import_module(manager_lib).run
        return loop.run_until_complete(manager(loop))

    else:
        # no test robot, no manager -> just run gazebo
        loop.run_until_complete(only_gazebo.run())
        loop.run_forever()


def main():
    import traceback

    def handler(_loop, context):
        try:
            exc = context['exception']
        except KeyError:
            print(context['message'])
            return

        if isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            sys.exit(0)

        if isinstance(exc, OSError) and exc.errno == 9:
            print(exc)
            traceback.print_exc()
            return

        # traceback.print_exc()
        raise exc

    try:
        arguments = parser.parse_args()
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handler)

        run(loop, arguments)

    except KeyboardInterrupt:
        print("Got CtrlC, shutting down.")

if __name__ == '__main__':
    # Making sure celery workers are killed before restarting, because otherwise
    # bugs will show up even though they are already fixed.

    print("STARTING")

    main()

    subprocess.Popen("pkill -9 -f 'celery worker'", shell=True)
    print("FINISHED")

    # Make sure the workers are terminated, if they still exist.
    # subprocess.run("pkill -f 'celery worker'", shell = True)
