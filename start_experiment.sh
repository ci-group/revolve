q#!/bin/bash
set -e
set -x

runs=1
runs_start=0
<<<<<<< HEAD
start_port=11520
exp_name=NSGA_BatteryCap_visualizationCum2
=======
start_port=15000
exp_name=battery_test_long_visualization3
>>>>>>> febbb65969709d667df4b381a319b66c1204f451
log_suffix=''
manager=experiments/battery/manager_reduced_joints_NSGA2.py

for i in $(seq $runs)
do
	run=$(($i+runs_start))
	screen -d -m -S "${exp_name}_${run}" -L -Logfile "${exp_name}${log_suffix}_${run}.log" nice -n19 ./revolve.sh --manager $manager --experiment-name $exp_name --n-cores 2 --port-start $((${start_port} + ($run*10))) --run $run
done
