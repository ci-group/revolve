#!/bin/bash
set -e
source .venv/bin/activate

export PATH=/home/karinemiras/Tools/gazebo/bin/:$PATH
export LD_LIBRARY_PATH=/home/karinemiras/Tools/gazebo/lib64

exec ./revolve.py $@

