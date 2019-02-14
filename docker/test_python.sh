#!/bin/bash
set -e

# Run Python unittests
cd /revolve
python3 -m unittest discover test_py/

