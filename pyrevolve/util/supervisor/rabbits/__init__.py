import os.path

import asyncio

from pyrevolve import parser
from .db_data import Robot, RobotEvaluation, RobotState
from .db_manage import PostgreSQLDatabase
from .celery_queue import CeleryQueue
from .gazebo_celery_worker_supervisor import GazeboCeleryWorkerSupervisor


async def celery_runner_command():
    arguments = parser.parse_args()

    # database: PostgreSQLDatabase = PostgreSQLDatabase()
    # await database.start()
    # database.init_db()

    celery_worker = GazeboCeleryWorkerSupervisor(
        world_file='worlds/plane.celery.world',
        gui=arguments.gui,
        simulator_args=['--verbose'],
        plugins_dir_path=os.path.join('.', 'build', 'lib'),
        models_dir_path=os.path.join('.', 'models'),
        simulator_name=f'GazeboCeleryWorker',
    )

    await celery_worker.launch_simulator(port=arguments.port_start)
    await asyncio.sleep(20)

    await celery_worker.wait()
    # database.disconnect()
    # database.destroy()

