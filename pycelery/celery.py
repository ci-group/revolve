
#!/usr/bin/env python3

# This file both starts the celery app and it does also define the tasks. These might
# better be split in the future, if the tasks get to large.

from __future__ import absolute_import, unicode_literals
from celery import Celery
from celery_pool_asyncio import monkey as cpa_monkey

# Starting Celery
cpa_monkey.patch()

app = Celery('pycelery')

# Setting configurations of celery.
app.conf.update(
    broker_url = 'amqp://guest@localhost//',
    result_backend = 'rpc://',
    task_serializer = 'json',
    result_serializer = 'json',
    accept_content = ['json'],
    enable_utc = True,
    result_expires = 3600,
    include = 'pycelery.tasks'
)

if __name__ == '__main__':
    app.start()
