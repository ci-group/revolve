#!/usr/bin/env sh

# Generate Python protobuf files
protoc -I ../cpprevolve/revolve/msgs \
       -I /usr/include/gazebo-9/gazebo/msgs/proto \
       --python_out=../pyrevolve/spec/msgs/ \
       ../cpprevolve/revolve/msgs/*.proto

# Correctly reference imported Gazebo messages
sed -E 's/import vector3d_pb2/from pygazebo.msg import vector3d_pb2/g' ../pyrevolve/spec/msgs/*.py
sed -E 's/import pose_pb2/from pygazebo.msg import pose_pb2/g' ../pyrevolve/spec/msgs/*.py
sed -E 's/import time_pb2/from pygazebo.msg import time_pb2/g' ../pyrevolve/spec/msgs/*.py
sed -E 's/import model_pb2/from pygazebo.msg import model_pb2/g' ../pyrevolve/spec/msgs/*.py

#it wont write the improt correctly. gotta change 'import' to 'from . import'
#in some cases 'from pygazebo.msg import'