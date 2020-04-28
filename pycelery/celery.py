# !/usr/bin/env python3

from celery import Celery, signals
from celery_pool_asyncio import monkey as cpa_monkey

# Starting Celery
cpa_monkey.patch()

app = Celery('pycelery')

app.control.purge()

# Setting configurations of celery.
app.conf.update(
    broker_url = 'pyamqp://localhost:5672//',
    result_backend = 'rpc://',
    task_serializer = 'yaml',
    result_serializer = 'json',
    accept_content = ['yaml', 'json'],
    enable_utc = True,
    result_expires = 3600,
    include = 'pycelery.tasks',
    worker_prefetch_multiplier = 2, # contacts works aslong as multiplier x child < 8
    task_acks_late = True,
    task_default_queue = 'robots',
    max_tasks_per_child = 2, # contacts worked with child = 1
    task_routes = ([
    ('pycelery.tasks.*', {'queue': 'robots'}),
    ('pycelery.tasks.hello', {'queue': 'celery'})],)
)

# THIS FUNCTION ALLOWS YOU TO SHUT DOWN LOGGING FOR ALL WORKERS.
# @signals.setup_logging.connect
# def setup_celery_logging(**kwargs):
#     """This function disables logging."""
#     pass

# app.log.setup()

if __name__ == '__main__':
    app.start()
