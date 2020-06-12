#!/bin/bash

port=${1:-6000}

for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_A --fitness displacement --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done

for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_B --fitness rotation --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done

for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_C --fitness gait_with_rotation --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done

for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_D --fitness gait_and_rotation --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done

for i in $(seq 1 10); do ./revolve.sh --experiment-name Experiment_E --fitness rotation_with_gait --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done
