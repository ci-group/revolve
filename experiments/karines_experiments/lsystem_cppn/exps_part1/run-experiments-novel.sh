#!/bin/bash

# run this bash first, and later run run-experiments-speed.sh

runs=20
runs_start=0
start_port=15000

experiments_path=karines_experiments/data/lsystem_cppn/
managers_path=experiments/karines_experiments/

# TODO: get experiments length instead
# num_exps-1
num_exps=1
experiments=("plasticoding" "hyperplasticoding")
managers=("lsystem_cppn/exps_part1/plasticoding_novel" "lsystem_cppn/exps_part1/hyperplasticoding_novel")

for i in $(seq $runs)
do
    run=$(($i+runs_start))

    for j in $(seq 0 $num_exps);
    do
      echo ""
	  screen -d -m -S "${experiments[j]}_${run}" -L -Logfile "${experiments[j]}_${run}.log" nice -n19 ./revolve.sh --manager "${managers_path}${managers[j]}.py" --experiment-name "${experiments_path}${experiments[j]}_${run}" --run-simulation 0  --run $run

    done
done