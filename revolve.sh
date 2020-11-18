#!/bin/bash
REVOLVE_DIR=$(dirname "$0")

source "$REVOLVE_DIR/.venv/bin/activate"
export LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
export PATH="$PATH"

exec ./revolve.py $@
