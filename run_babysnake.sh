#!/bin/bash
set -e
set -x

screen -d -m -S "BabySnake" -L -Logfile "babySnakeA.log" nice -n19 python3 ./experiments/bo_learner/GridSearchBaby.py
