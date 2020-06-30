#!/bin/bash
set -e
set -x

screen -d -m -S "BabyA" -L -Logfile "babyA.log" nice -n19 python3 ./experiments/bo_learner/GridSearchBaby.py
