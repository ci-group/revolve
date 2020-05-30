#!/usr/bin/env python3
import subprocess

runs=[1,2,3,4,5,6,7,8]#range(1,11)
start_port=14000
exp_name='SpeedUpAnalyzer'
log_suffix=''
manager='experiments/examples/manager_pop.py'

if __name__ == "__main__":
    for run in runs:
        run_start_port = start_port + (run*10)
        process = ['screen','-d','-m',
            '-S',f'{exp_name}_{run}',
            '-L','-Logfile',f"{exp_name}{log_suffix}_{run}.log",
            'nice','-n19',
            './revolve.py','--manager',manager,
            '--experiment-name',exp_name,
            '--n-cores','4',
            '--port-start',str(run_start_port),
            '--run',str(run)
            ]
        print("starting" + " ".join(process))
        subprocess.call(process)
