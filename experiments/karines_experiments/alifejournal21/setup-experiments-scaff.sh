#!/bin/bash
#set -e
#set -x

runs=20
#num_terminals=8
num_terminals=4
start_port=8000
final_gen=99
experiments=("scaffeq" "scaffeqinv" "scaffinc" "scaffincinv")
experiments_path=link_storage/alifej2021/
managers_path=experiments/karines_experiments/alifejournal21/

while true
	do

    echo "killing all processes..."
    kill $(  ps aux | grep 'gzserver' | awk '{print $2}');
    kill $(  ps aux | grep 'revolve.py' | awk '{print $2}');

    echo "restarting all processes..."

    to_do=()
    done_gen=()

    for i in $(seq $runs)
    do
        run=$(($i))

        for experiment in "${experiments[@]}"
        do

         echo ""
         file="${experiment}_${run}.log";

         #check experiments status
         if [[ -f "$file" ]]; then
            value=$(grep "Exported snapshot" $file|tail -n1|sed -E "s/\[(.*),.*Exported snapshot ([0-9]+).*/\2/g");
            echo $file;
            echo $value;
            if [ "$value" != "$final_gen" ]; then
              to_do+=("${experiment}_${run}")
              done_gen+=("${value}")
             fi
          else
             echo "$file"
             echo "None";
             to_do+=("${experiment}_${run}")
              done_gen+=(-1)
          fi

        done
    done

    # selects num_terminals unfinished experiments to spawn
    to_do=(${to_do[@]:0:$num_terminals})
    i=0
    for experiment in "${to_do[@]}"
    do

         if [ $(cut -d'_' -f1 <<<"$experiment") == "scaffeq" ]; then
             gens=(0 17 34 51 68 85)
             worlds=("plane" "tilted1" "tilted2" "tilted3" "tilted4" "tilted5")
         fi
         if [ $(cut -d'_' -f1 <<<"$experiment") == "scaffeqinv" ]; then
             gens=(0 17 34 51 68 85)
             worlds=("tilted5" "tilted4" "tilted3" "tilted2" "tilted1" "plane")
         fi
         if [ $(cut -d'_' -f1 <<<"$experiment") == "scaffinc" ]; then
             gens=(0 4 13 27 46 70)
             worlds=("plane" "tilted1" "tilted2" "tilted3" "tilted4" "tilted5")
         fi
         if [ $(cut -d'_' -f1 <<<"$experiment") == "scaffincinv" ]; then
             gens=(0 4 13 27 46 70)
             worlds=("tilted5" "tilted4" "tilted3" "tilted2" "tilted1" "plane")
         fi

         if [ $((${done_gen[$i]}+1)) -ge ${gens[0]} ] && [ $((${done_gen[$i]}+1)) -lt ${gens[1]} ]; then
           world=0
         fi
         if [ $((${done_gen[$i]}+1)) -ge ${gens[1]} ] && [ $((${done_gen[$i]}+1)) -lt ${gens[2]} ]; then
           world=1
         fi
         if [ $((${done_gen[$i]}+1)) -ge ${gens[2]} ] && [ $((${done_gen[$i]}+1)) -lt ${gens[3]} ]; then
           world=2
         fi
         if [ $((${done_gen[$i]}+1)) -ge ${gens[3]} ] && [ $((${done_gen[$i]}+1)) -lt ${gens[4]} ]; then
           world=3
         fi
         if [ $((${done_gen[$i]}+1)) -ge ${gens[4]} ] && [ $((${done_gen[$i]}+1)) -lt ${gens[5]} ]; then
           world=4
         fi
         if [ $((${done_gen[$i]}+1)) -ge ${gens[5]} ]; then
           world=5
         fi

         resimulate=""
         for gen in "${gens[@]}"
          do   resimulate="$resimulate$gen-"
         done

         echo "${experiment} $((${done_gen[$i]}+1)) ${worlds[$world]}"
         screen -d -m -S "${experiment}" -L -Logfile "${experiment}.log" nice -n19 ./revolve.sh --manager "${managers_path}scaffolding.py" --world "${worlds[$world]}" --experiment-name "${experiments_path}${experiment}" --resimulate "${resimulate}" --evaluation-time 50 --n-cores 4 --port-start $start_port
         start_port=$((${start_port}+10))
         i=$((${i}+1))
    done

  sleep 1800s;

done


# killall screen
# screen -r naaameee
# screen -list