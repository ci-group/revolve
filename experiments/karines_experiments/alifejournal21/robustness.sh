#!/bin/bash


experiments=("scaffeq" "staticplane" "scaffeqinv" "scaffinc" "scaffincinv" "statictilted")
environments=("plane" "tilted5")
runs=20

for i in $(seq $runs)
do
    run=$(($i))

    for experiment in "${experiments[@]}"
    do
       for environment in "${environments[@]}"
          do
              ./revolve.py --watch-type log --n-cores 4 --evaluation-time 50 --experiment-name link_storage/alifej2021/${experiment}_$i  --manager experiments/karines_experiments/alifejournal21/watch_robust.py --world ${environment} --watch-k 100 --watch-gen 99 --port-start 5675
          done
    done
done
