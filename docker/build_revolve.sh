#!/bin/bash
set -e

# Build Revolve
cd /revolve
mkdir -p build && cd build
cmake ../cpp \
      -DCMAKE_BUILD_TYPE="Release"
make -j4

# Set the virtual environment
cd /revolve
virtualenv .venv
source .venv/bin/activate
pip install -r requiremenrst.txt
