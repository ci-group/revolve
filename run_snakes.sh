#!/bin/bash
set -e
set -x

screen -d -m -S "Snakes" -L -Logfile "snakes6.log" nice -n19 python3 ./experiments/bo_learner/GridSearch.py
