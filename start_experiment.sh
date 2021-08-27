#!/bin/bash
set -e
set -x

runs=10
runs_start=0

start_port=11520
exp_name=evolution_cmaes

log_suffix=''
manager=experiments/jlo/learning_cppn_directed.py

for i in $(seq $runs)
do
        run=$(($i+runs_start))
        screen -d -m -S "${exp_name}_${run}" -L -Logfile "${exp_name}${log_suffix}_${run}.log" nice -n19 ./revolve_restarting.sh --manager $manager --experiment-name $exp_name --n-cores 5 --port-start $((${start_port} + ($run*10))) --run $run --evaluation-time=50 --learner=cmaes --recovery-enabled=true
done
