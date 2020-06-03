#!/usr/bin/env python3

import subprocess
import time
"""This file is used to run multiple celery experiments after another. Can be run
using ./multiple-runs.py"""

runs = 17
manager = "pycelery/manager.py"
cores = 32

for i in range(runs):
    p = subprocess.Popen(f"./revolve.py --manager {manager} --world worlds/celeryplane.world --n-cores {cores} --run {i}", shell=True)
    p.wait()
    p.terminate()
    time.sleep(10) #give time for celery to cancel.
    print(f"Run {i} done\n")
