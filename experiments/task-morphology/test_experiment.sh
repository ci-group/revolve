#!/bin/bash

port=${1:-6000}

for i in $(seq 1 1); do ./revolve.sh --experiment-name Test_Experiment --fitness displacement --simulator-cmd=gzserver --manager experiments/task-morphology/manager_test.py --port-start=$port --world worlds/plane.world --recovery-enabled True; done
