#!/bin/bash
set -e
set -x


#for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_A --fitness displacement --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done

#for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_B --fitness rotation --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done

#for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_C --fitness gait_with_rotation --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done

#for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_D --fitness gait_and_rotation --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done

#for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_E --fitness rotation_with_gait --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done


runs=10
runs_start=0
start_port=13000
exp_name=Experiment_E
fitness=rotation_with_gait
log_suffix=''
manager=experiments/task-morphology/manager.py

for i in $(seq $runs)
do
	run=$(($i+runs_start))
	screen -d -m -S "${exp_name}_${run}" -L -Logfile "${exp_name}${log_suffix}_${run}.log" nice -n19 ./revolve.sh --manager $manager --experiment-name $exp_name --fitness $fitness --n-cores 4 --port-start $((${start_port} + ($run*10))) --run $run
done
