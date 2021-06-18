unset QT_QPA_PLATFORM
unset XDG_SESSION_TYPE
export LD_LIBRARY_PATH=/usr/local/lib/
export GAZEBO_PLUGIN_PATH=$PWD/build/lib
export GAZEBO_MODEL_PATH=$PWD/models
exec $@
