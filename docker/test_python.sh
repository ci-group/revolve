#!/bin/bash
set -e

# Run Python unittests
cd /revolve
python -m unittest discover test_py/
