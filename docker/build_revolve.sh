#!/bin/bash
set -e

# Build Revolve
cd /revolve
mkdir -p build && cd build
cmake ../cpprevolve \
      -DCMAKE_BUILD_TYPE="Release"
make -j4

# Install the Python dependencies
cd /revolve
pip3 install -r requirements.txt
