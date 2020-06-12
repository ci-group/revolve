#!/bin/bash

port=${1:-6000}

for i in $(seq 1 1); do ./revolve.sh --experiment-name Test_Experiment --fitness displacement --simulator-cmd=gzserver --manager experiments/task-morphology/manager.py --port-start=$port --world worlds/plane.world ; done
