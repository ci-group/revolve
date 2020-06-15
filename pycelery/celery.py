# !/usr/bin/env python3

from celery import Celery, signals
from celery_pool_asyncio import monkey as cpa_monkey
from pyrevolve import parser

# Starting Celery
cpa_monkey.patch()

app = Celery('pycelery')

# Setting configurations of celery.
app.conf.update(
    broker_url = 'pyamqp://localhost:5672//',
    result_backend = 'rpc://',
    task_serializer = 'yaml',
    result_serializer = 'json',
    accept_content = ['yaml', 'json'],
    enable_utc = True,
    result_expires = 600,
    result_persistant = False,
    include = 'pycelery.tasks',
    worker_prefetch_multiplier = 1, # contacts works aslong as multiplier x child < 8
    task_acks_late = True,
    max_tasks_per_child = 2, # contacts worked with child = 1
)

# THIS FUNCTION ALLOWS YOU TO SHUT DOWN LOGGING FOR ALL WORKERS.
# @signals.setup_logging.connect
# def setup_celery_logging(**kwargs):
#     """This function disables logging."""
#     pass

# app.log.setup()

if __name__ == '__main__':
    app.start()
