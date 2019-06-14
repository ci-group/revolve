# CMake Required Version
cmake_minimum_required (VERSION 3.12.1)

# Project name
project (Revolve)
set (CMAKE_CXX_STANDARD 11)

# Include cmake subdirectories
add_subdirectory(revolve/brains)

if (NOT BUILD_ONLY_BRAIN)
    add_subdirectory(revolve/gazebo)
endif()

if (BUILD_RASPBERRY)
    add_subdirectory(revolve/raspberry)
endif()
