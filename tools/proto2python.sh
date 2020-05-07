#!/bin/bash

set -e

PROTO_FOLDER='../cpprevolve/revolve/gazebo/msgs'
GAZEBO_PROTO_FOLDER='/usr/include/gazebo-9/gazebo/msgs/proto'
PY_PROTOBUF_FOLDER='../pyrevolve/spec/msgs/'

# Generate Python protobuf files
protoc -I ${PROTO_FOLDER} \
       -I ${GAZEBO_PROTO_FOLDER} \
       --python_out=${PY_PROTOBUF_FOLDER} \
       ${PROTO_FOLDER}/*.proto

# Correctly reference imported Gazebo messages
sed -i -E 's/import vector3d_pb2/from pygazebo.msg import vector3d_pb2/g' ${PY_PROTOBUF_FOLDER}/*.py
sed -i -E 's/import pose_pb2/from pygazebo.msg import pose_pb2/g' ${PY_PROTOBUF_FOLDER}/*.py
sed -i -E 's/import time_pb2/from pygazebo.msg import time_pb2/g' ${PY_PROTOBUF_FOLDER}/*.py
sed -i -E 's/import model_pb2/from pygazebo.msg import model_pb2/g' ${PY_PROTOBUF_FOLDER}/*.py

sed -i -E 's/import body_pb2/from . import body_pb2/g' ${PY_PROTOBUF_FOLDER}/*.py
sed -i -E 's/import parameter_pb2/from . import parameter_pb2/g' ${PY_PROTOBUF_FOLDER}/*.py
sed -i -E 's/import neural_net_pb2/from . import neural_net_pb2/g' ${PY_PROTOBUF_FOLDER}/*.py

#it wont write the improt correctly. gotta change 'import' to 'from . import'
#in some cases 'from pygazebo.msg import'