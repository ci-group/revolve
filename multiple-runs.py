#!/usr/bin/env python3

import subprocess

"""This file is used to run multiple celery experiments after another. Can be run
using ./multiple-runs.py"""

runs = 10
manager = "pycelery/manager.py"
cores = 32

for i in range(runs):
    p = subprocess.Popen(f"./revolve.py --manager {manager} --n-cores {cores} --run {i}", shell=True)
    p.wait()
    p.terminate()
    print(f"Run {i} done")
