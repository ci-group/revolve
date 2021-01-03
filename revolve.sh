#!/bin/bash
REVOLVE_DIR=$(dirname "$0")

source "$REVOLVE_DIR/.venv/bin/activate"
#export LD_LIBRARY_PATH="~/Tools/gazebo/lib64/:$LD_LIBRARY_PATH"
#export PATH="~/Tools/gazebo/bin/:$PATH"

exec ./revolve.py $@
