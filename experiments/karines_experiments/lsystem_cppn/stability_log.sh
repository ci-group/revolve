#!/bin/bash
set -e
set -x

experiments=("plasticoding" "hyperplasticoding")
runs=20
times=(30 60)

for i in $(seq $runs)
do
    run=$(($i))

    for experiment in "${experiments[@]}"
    do

        for time in "${times[@]}"
        do
               ./revolve.py --watch-type log --evaluation-time $time --experiment-name link_storage/lsystem_cppn/lsystem_cppn/${experiment}_$i  --manager experiments/karines_experiments/watch_best.py

        done
    done
done
