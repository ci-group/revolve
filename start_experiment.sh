#!/bin/bash
set -e
set -x

runs=10
runs_start=0
start_port=15000
exp_name=expHeritability
log_suffix='_tenebra'
manager=experiments/heritability/manager.py

for i in $(seq $runs)
do
	run=$(($i+runs_start))
	screen -d -m -S "${exp_name}_${run}" -L -Logfile "${exp_name}${log_suffix}_${run}.log" nice -n19 ./revolve.sh --manager $manager --experiment-name $exp_name --n-cores 4 --port-start $((${start_port} + ($run*10))) --run $run
done
