from __future__ import absolute_import, unicode_literals
import asyncio
import time
import subprocess
import os, sys
import random

from .celery import app
from celery import group, signature
from pycelery.tasks import calculation_of_primes
from pycelery.celerycontroller import CeleryController
from pyrevolve import revolve_bot, parser

async def run():
    """A file to compare celery methods with each other."""

    settings = parser.parse_args()
    celerycontroller = CeleryController(settings) # Starting celery

    await asyncio.sleep(5) # Celery needs time

    # 500 celery tasks.
    calcs = [10000 for i in range(5)]

    # Start recording time
    begin = time.time()

    future = []
    for i in calcs:
        future.append(await calculation_of_primes.delay(i))

    result = []
    for i in future:
        result.append(await i.get())

    # end recording time.
    end = time.time()
    print(f'run of seperate: {end-begin}')
    """UNTIL HERE IT WORKS FINE!"""

    begin2 = time.time()

    job = group(
             calculation_of_primes.s(10000),
             calculation_of_primes.s(10000),
             calculation_of_primes.s(10000),
             calculation_of_primes.s(10000),
             calculation_of_primes.s(10000))

    res = job.apply_async()
    result = res.get()

    end2 = time.time()

    print(f'run of together: {end2-begin2}')



    subprocess.Popen("pkill -9 -f 'celery worker'", shell=True)

    await asyncio.sleep(5)
