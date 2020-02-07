#!/usr/bin/env python3

import subprocess

"""This file is used to run multiple celery experiments after another. Can be run
using ./multiple-runs.py"""

runs = 5
manager = "pycelery/manager.py"
cores = 7

for i in range(10):
    p = subprocess.Popen("./revolve.py --manager "+ manager + " --n-cores "+str(cores)+" --experiment-name default_exp_"+str(i), shell=True)
    p.wait()
    p = subprocess.Popen("pkill -9 -f 'gzserver'", shell=True)
    p.wait()
    print(f"run {i} done")
