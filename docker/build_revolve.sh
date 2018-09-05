#!/bin/bash
set -e

# Build Revolve
cd /revolve
mkdir -p build && cd build
cmake ../cpp \
      -DCMAKE_BUILD_TYPE="Release"
make -j4

# Install the Python dependencies
cd /revolve
pip install -r requirements.txt
