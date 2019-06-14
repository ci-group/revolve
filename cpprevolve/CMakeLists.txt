# CMake Required Version
cmake_minimum_required (VERSION 3.12.1)

# Project name
project (Revolve)

# Include cmake subdirectories
add_subdirectory(revolve/brains)

if (NOT ${BUILD_ONLY_BRAIN})
    add_subdirectory(revolve/gazebo)
endif()
