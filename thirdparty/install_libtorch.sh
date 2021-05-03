#!/bin/bash

set -e
set -x

# Ensure these packages are installed:
# -  python3-typing-extensions
# -  libsleef-dev

cd pytorch
#rm -rf build
mkdir -p build
cd build

cmake -DBUILD_PYTHON=False -DBUILD_TEST=False -DBUILD_TORCH=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local/ -DCUDNN_LIBRARY=/usr/local/cuda/lib64 -DNUMPY_INCLUDE_DIR=/usr/lib/python3/dist-packages/numpy/core/include -DPYTHON_EXECUTABLE=/usr/bin/python3 -DTORCH_BUILD_VERSION=1.8.1 -DUSE_CUDA=ON -DUSE_NNPACK=1 -DUSE_NUMPY=True -DUSE_OPENCV=1 -DUSE_SYSTEM_CPUINFO=OFF -DUSE_SYSTEM_SLEEF=ON -DBUILD_CUSTOM_PROTOBUF=OFF -DUSE_SYSTEM_PTHREADPOOL=OFF ..

make -j16
