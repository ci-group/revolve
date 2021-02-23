#!/bin/bash

set -x

runs=20
final_gen=149
num_terminals=8
start_port=8000
experiments=("plasticoding-rep" "hyperplasticoding-rep")
managers_sulfix=("_speed" "_speed")
experiments_path=karines_experiments/data/lsystem_cppn_2/
managers_path=experiments/karines_experiments/lsystem_cppn/exps_part2/

while true
	do

    echo "killing all processes..."
    kill $(  ps aux | grep 'gzserver' | awk '{print $2}');
    kill $(  ps aux | grep 'revolve.py' | awk '{print $2}');

    echo "restarting all processes..."

    to_do=()

    for i in $(seq $runs)
    do
        run=$(($i))

        for experiment in "${experiments[@]}"
        do

         echo ""
         file="${experiment}_${run}.log";

         #check if experiments status
         if [[ -f "$file" ]]; then

            value=$(grep "Exported snapshot" $file|tail -n1|sed -E "s/\[(.*),.*Exported snapshot ([0-9]+).*/\2/g");
            echo $file;
            echo $value;
            if [ "$value" != "$final_gen" ]; then
              to_do+=("${experiment}_${run}")
             fi
          else
             echo "$file"
             echo "None";
             to_do+=("${experiment}_${run}")
          fi

        done
    done


    # selects num_terminals unfinished experiments to spawn
    to_do=(${to_do[@]:0:$num_terminals})
    for experiment in "${to_do[@]}"
    do
         echo ""
         screen -d -m -S "${experiment}" -L -Logfile "${experiment}.log" nice -n19 ./revolve.sh --manager "${managers_path}$(cut -d'_' -f1 <<<"$experiment")${managers_sulfix}.py" --experiment-name "${experiments_path}${experiment}"   --n-competing-children 50 --n-cores 4 --port-start $start_port
         start_port=$((${start_port}+10))
    done

    sleep 1800s;

done



# killall screen
# screen -r naaameee