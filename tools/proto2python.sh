#!/usr/bin/env sh

# Generate Python protobuf files
protoc -I ../cpprevolve/revolve/msgs \
       -I /usr/local/include/gazebo-9/gazebo/msgs/proto \
       --python_out=../pyrevolve/spec/msgs/ \
       ../cpprevolve/revolve/msgs/*.proto

# Correctly reference imported Gazebo messages
sed -E 's/import vector3d_pb2/from pygazebo.msg import vector3d_pb2/g' ../revolve/spec/msgs/*.py
sed -E 's/import pose_pb2/from pygazebo.msg import pose_pb2/g' ../revolve/spec/msgs/*.py
sed -E 's/import time_pb2/from pygazebo.msg import time_pb2/g' ../revolve/spec/msgs/*.py
sed -E 's/import model_pb2/from pygazebo.msg import model_pb2/g' ../revolve/spec/msgs/*.py
