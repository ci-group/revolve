#!/usr/bin/env python3

import subprocess
import time
"""This file is used to run multiple celery experiments after another and SHOULD NOT be
used for multiple parallel experiments. Can be run
using ./multiple-consecutive-runs.py"""

runs = 8 
manager = "pycelery/manager.py"
cores = 8

for i in range(runs):
    print(f"-----Run {i}-----\n")
    p = subprocess.Popen(f"./revolve.py --manager {manager} --world worlds/celeryplane.world --n-cores {cores} --run {i}", shell=True)
    p.wait()
    p.terminate()
    subprocess.Popen("pkill -9 -f 'celery worker'", shell=True)
    subprocess.Popen("pkill -9 -f 'gzserver'", shell=True)

    time.sleep(30) #give time for celery and gazebo to shutdown.
