#!/bin/bash
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
BASE=$DIR/../../build
ANALYZER=$BASE/body-analyzer
ANALYZER_TOOL=1 GAZEBO_PLUGIN_PATH=$GAZEBO_PLUGIN_PATH:$BASE/lib $ANALYZER analyzer-world.world
