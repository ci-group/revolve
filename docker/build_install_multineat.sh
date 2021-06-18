#!/bin/bash
set -e

# Build Revolve
cd /revolve/thirdparty/MultiNEAT

mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE="Release"
make -j4
make -j4 install
cd ..
rm -r build
