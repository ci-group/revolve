#!/usr/bin/env python3
import subprocess
import time

number_of_experiments = 3
start_port=14000
cores = 8
exp_name='SpeedUpAnalyzer'
log_suffix=''
manager='pycelery/manager.py'
world= 'worlds/celeryplane.world'

if __name__ == "__main__":
    for run in range(number_of_experiments):
        run_start_port = start_port + (run*cores*2)
        process = ['screen','-d','-m',
            '-S',f'{exp_name}_{run}',
            '-L','-Logfile',f"{exp_name}{log_suffix}_{run}.log",
            'nice','-n19',
            './revolve.py','--manager',manager,
            '--n-cores',str(cores),
            '--port-start',str(run_start_port),
            '--run',str(run),
            '--world', world
            ]
        print("starting" + " ".join(process))
        subprocess.call(process)

        time.sleep(30) # Let the process start without other interference.
