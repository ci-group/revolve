#!/bin/bash
set -e

# Build Revolve
cd /revolve

# use version 10
sed -i 's/    find_package(gazebo 9 REQUIRED)/    find_package(gazebo 10 REQUIRED)/g' cpprevolve/revolve/gazebo/CMakeLists.txt

mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE="Release"
make -j4

# Install the Python dependencies
cd /revolve
pip3 install scikit-build
pip3 install cmake
PATH=/usr/local/bin:$PATH pip3 install -r requirements.txt
pip3 uninstall cmake -y
