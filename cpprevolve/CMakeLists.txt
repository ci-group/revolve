# CMake Required Version
cmake_minimum_required (VERSION 2.8.12)

# Project name
project (Revolve)

# _____________________________________________________________________________

# Added for BO
# Allow Eigen/core to be included via <Eigen/core>

# Initial setups
# _____________________________________________________________________________
# CMake flag to help local projects find the build dir
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../build/lib")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../build/lib")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../build")
set(HEADER_COPY_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../build/include")

# Copy header files to the output directory so they can be used
# by other projects in development.
file(
   COPY ${CMAKE_CURRENT_SOURCE_DIR}/revolve
   DESTINATION ${HEADER_COPY_DIR}
   FILES_MATCHING PATTERN "*.h"
)
message("Using local build directory.")

# Pass source dir to preprocessor
add_definitions(-DSOURCE_DIR=${CMAKE_SOURCE_DIR})

# Compiler options
# TODO This currently assumes GCC, add Windows support in due time
add_definitions(-pedantic -Wno-long-long -Wall -Wextra -Wformat=2
                -Wredundant-decls -Wwrite-strings -Wmissing-include-dirs 
                -Wswitch-enum -Wuninitialized 
                -Wswitch-default -Winit-self -Wfloat-equal -fPIC )

# Use C++11 (removed - the Gazebo flags below do this)
# set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

# Debug Flags 
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -ggdb3 -DDEBUG")

# Release flags
#set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -funroll-loops -finline-functions -fomit-frame-pointer -DNDEBUG")

# MacOS X needed variables
if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
  # adaptable according to individual needs
  set(CMAKE_MACOSX_RPATH ON)
  #    set(CMAKE_SKIP_BUILD_RPATH FALSE)
  #    set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
  #    set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
  #    set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
endif ()


# NLopt (for limbo)
set(NLOPT_INCLUDE_DIR "/home/maarten/Documents/nlopt/build/")
find_package(NLOpt REQUIRED)
include_directories(${NLOPT_INCLUDE_DIR})

# Limbo
# set(LIMBO_DIR /usr/include/limbo/)
#file(GLOB headers /usr/include/limbo/src/limbo/*.hpp)
#message("Headers are" )
#foreach(variable_name ${headers})
#    message(${variable_name})
#endforeach()

#find_package(LIMBO REQUIRED PATHS /usr/include/limbo/build)
#include_directories(/usr/include/limbo)

#include_directories(/home/maarten/projects/revolve-simulator/revolve/limbo)

find_package(Eigen3 REQUIRED)
include_directories(${EIGEN3_INCLUDE_DIR})


# Finding dependencies
# _____________________________________________________________________________



# Find Boost
find_package(Boost REQUIRED COMPONENTS system)
include_directories(${Boost_INCLUDE_DIRS})

# Find GSL - GNU Scientific Library
find_package(GSL REQUIRED)
include_directories(${GSL_INCLUDE_DIRS})

find_package(yaml-cpp REQUIRED)
include_directories(${YAML_CPP_INCLUDE_DIR})

# Find Gazebo
# LOCAL_GAZEBO_DIR can be set to a path with a gazebo-config.cmake
if (LOCAL_GAZEBO_DIR)
    find_package(gazebo 9 REQUIRED CONFIG
            PATHS "${LOCAL_GAZEBO_DIR}"
            NO_DEFAULT_PATH)
    message(WARNING "Using local Gazebo @ ${gazebo_DIR}")
else()
    find_package(gazebo 9 REQUIRED)
endif()
include_directories(${GAZEBO_INCLUDE_DIRS})
link_directories(${GAZEBO_LIBRARY_DIRS})

# Find Protobuf
# TODO: This part is currently a mess, and it should be handeled better
find_package(Protobuf REQUIRED)

# Find the Protobuf import directory for Gazebo. Found in this
# tutorial: http://gazebosim.org/tutorials?tut=custom_messages&cat=transport
set(GAZEBO_PROTOBUF_DIR)
foreach(ITR ${GAZEBO_INCLUDE_DIRS})
  if(ITR MATCHES ".*gazebo-[0-9.]+$")
    set(GAZEBO_PROTO_PATH "${ITR}/gazebo/msgs/proto")
    set(GAZEBO_PROTO_INCLUDE "${ITR}/gazebo/msgs")
  endif()
endforeach()
include_directories(
    ${CMAKE_SOURCE_DIR}
    ${PROTOBUF_INCLUDE_DIRS}
    ${GAZEBO_PROTO_INCLUDE}
)


# Add Gazebo C++ flags (this includes c++11)
list(APPEND CMAKE_CXX_FLAGS "${GAZEBO_CXX_FLAGS}")

# Directory where the .proto files reside within revolve
set(SPEC_DIR "${CMAKE_SOURCE_DIR}/cpprevolve/revolve/msgs")
message(${SPEC_DIR})

# All protobuf files we need, including the Gazebo ones
file(GLOB_RECURSE REVOLVE_PROTOS ${SPEC_DIR}/*.proto)

# Do the protobuf generation by hand for more flexibility. The files are
# generated in a subdirectory such that it can potentially be added to the
# include path for work-in-progress projects I co-develop with this.
# Copied most of this code from
# http://stackoverflow.com/questions/29346488/protobuf-generate-cpp-not-generating-src-and-header-files
# Also see
# https://github.com/Kitware/CMake/blob/master/Modules/FindProtobuf.cmake
set(PROTO_SRCS)
set(PROTO_HDRS)
if (HEADER_COPY_DIR)
    set(PROTO_OUTPUT_BASE ${HEADER_COPY_DIR})
else()
    set(PROTO_OUTPUT_BASE ${CMAKE_CURRENT_BINARY_DIR})
endif()

# Include the directory where the protobuf files will be placed
include_directories(${PROTO_OUTPUT_BASE})


file(MAKE_DIRECTORY ${PROTO_OUTPUT_BASE}/revolve/msgs)
foreach(RV_PROTO ${REVOLVE_PROTOS})
    get_filename_component(RV_ABS_PROTO ${RV_PROTO} ABSOLUTE)
    get_filename_component(RV_NAME_PROTO ${RV_PROTO} NAME_WE)
    get_filename_component(RV_DIR_PROTO ${RV_PROTO} DIRECTORY)

    list(APPEND PROTO_SRCS
         "${PROTO_OUTPUT_BASE}/revolve/msgs/${RV_NAME_PROTO}.pb.cc")
    list(APPEND PROTO_HDRS
         "${PROTO_OUTPUT_BASE}/revolve/msgs/${RV_NAME_PROTO}.pb.h")

    add_custom_command(
      OUTPUT "${PROTO_OUTPUT_BASE}/revolve/msgs/${RV_NAME_PROTO}.pb.cc"
             "${PROTO_OUTPUT_BASE}/revolve/msgs/${RV_NAME_PROTO}.pb.h"
      COMMAND  ${PROTOBUF_PROTOC_EXECUTABLE}
      ARGS -I ${RV_DIR_PROTO}
           -I ${GAZEBO_PROTO_PATH}
           --cpp_out ${PROTO_OUTPUT_BASE}/revolve/msgs ${RV_ABS_PROTO}
      DEPENDS ${RV_ABS_PROTO}
      COMMENT "Running C++ protocol buffer compiler on ${RV_PROTO}"
      VERBATIM )
endforeach()

# Tell the compiler these files were generated
set_source_files_properties(
    ${PROTO_SRCS} ${PROTO_HDRS} PROPERTIES GENERATED TRUE)

# Source subdirectories
# _____________________________________________________________________________

# Plugin C++ files
file(GLOB_RECURSE
     REVOLVE_GZ_SRC
     revolve/gazebo/brains/*.cpp
     revolve/gazebo/motors/*.cpp
     revolve/gazebo/sensors/*.cpp
     revolve/gazebo/util/*.cpp
     revolve/gazebo/plugin/BodyAnalyzer.cpp
     revolve/gazebo/plugin/RobotController.cpp
     revolve/gazebo/plugin/WorldController.cpp
)

# Generate
# _____________________________________________________________________________
# Add the file that registers the body analyzer as a separate library that
# can be used as a world plugin directly.
# Create the library containing the Revolve API

# Generate spec library with the messages
add_library(
    revolve-proto STATIC
    ${PROTO_SRCS}
)


set_target_properties(revolve-proto PROPERTIES LINKER_LANGUAGE CXX)
target_link_libraries(
    revolve-proto
    ${PROTOBUF_LIBRARIES}
    nlopt
)

# Create Revolve bundle plugin
add_library(
    revolve-gazebo
    ${REVOLVE_GZ_SRC}
    revolve/gazebo/brains/DifferentialCPG_BO.h revolve/gazebo/brains/RLPower.h)


target_link_libraries(
    revolve-gazebo
    ${GAZEBO_LIBRARIES}
    ${Boost_LIBRARIES}
    ${GSL_LIBRARIES}
    ${YAML_CPP_LIBRARIES}
)

# Create World plugin
add_library(
    WorldControlPlugin SHARED
    revolve/gazebo/plugin/register_world_plugin.cpp
)
target_link_libraries(
    WorldControlPlugin
    revolve-gazebo
    revolve-proto
    ${GAZEBO_LIBRARIES}
)

# Create Robot plugin
add_library(
    RobotControlPlugin SHARED
    revolve/gazebo/plugin/register_robot_plugin.cpp
)
target_link_libraries(
    RobotControlPlugin
    revolve-gazebo
    revolve-proto
    ${GAZEBO_LIBRARIES}
)

# Install
# _____________________________________________________________________________
# Install libraries into "lib", header files into "include"

install(
    TARGETS revolve-proto revolve-gazebo
    DESTINATION lib
)

install(
   DIRECTORY revolve
   DESTINATION include
   FILES_MATCHING PATTERN "*.h"
)
