#!/bin/bash
set -e
set -x

# run this bash first, and later run run-experiments-speed.sh

#20
runs=19
runs_start=0

experiments_path=karines_experiments/data/lsystem_cppn/
managers_path=experiments/karines_experiments/

# TODO: get experiments length instead
# num_exps-1
num_exps=1
experiments=("plasticoding_rep" "hyperplasticoding_rep")
managers=("lsystem_cppn/exps_part2/plasticoding_novel_rep" "lsystem_cppn/exps_part2/hyperplasticoding_novel_rep")

for i in $(seq $runs)
do
    run=$(($i+runs_start))

    for j in $(seq 0 $num_exps);
    do
      echo ""
	  screen -d -m -S "${experiments[j]}_${run}" -L -Logfile "${experiments[j]}_${run}.log" nice -n19 ./revolve.sh --manager "${managers_path}${managers[j]}.py" --experiment-name "${experiments_path}${experiments[j]}_${run}" --run-simulation 0  --run $run

    done
done