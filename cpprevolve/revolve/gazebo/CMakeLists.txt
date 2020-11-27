# Initial setups
# _____________________________________________________________________________

# CMake flag to help local projects find the build dir
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/build/lib")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/build/lib")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/build")

include_directories(${CMAKE_SOURCE_DIR}/cpprevolve)

# Pass source dir to preprocessor
add_definitions(-DSOURCE_DIR=${CMAKE_SOURCE_DIR})

# Compiler options
# TODO This currently assumes GCC, add Windows support in due time
add_definitions(-pedantic -Wno-long-long -Wall -Wextra -Wformat=2
        -Wredundant-decls -Wwrite-strings -Wmissing-include-dirs
        -Wswitch-enum -Wuninitialized
        -Wswitch-default -Winit-self -Wfloat-equal -fPIC )

set (CMAKE_CXX_STANDARD 11)

# Debug Flags
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -ggdb3 -DDEBUG")

# Release flags
#set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -funroll-loops -finline-functions -fomit-frame-pointer -DNDEBUG")

# MacOS X needed variables
if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    # adaptable according to individual needs
    set(CMAKE_MACOSX_RPATH ON)
    #set(CMAKE_SKIP_BUILD_RPATH FALSE)
    #set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
    #set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
    #set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
endif ()


# Finding dependencies
# _____________________________________________________________________________


# PKG-CONFIG
find_package(PkgConfig REQUIRED)

# Find Boost
find_package(Boost REQUIRED COMPONENTS system)
include_directories(${Boost_INCLUDE_DIRS})

# Find Eigen3 - A lightweight C++ template library for vector and matrix math
find_package(Eigen3 REQUIRED)
include_directories(${EIGEN3_INCLUDE_DIR})

# Find NLOpt - Non Linear Optimization
pkg_check_modules(NLOpt REQUIRED nlopt>=2.4)
include_directories(${NLOpt_INCLUDE_DIRS})
link_directories(${NLOpt_LIBRARY_DIRS})

# Find Limbo - LIbrary for Model-Based Optimization
set(LIMBO_DIR ${CMAKE_SOURCE_DIR}/thirdparty/limbo)
set(LIMBO_DEFINES USE_NLOPT)
include_directories(${LIMBO_DIR}/src)

# Find GSL - GNU Scientific Library
find_package(GSL REQUIRED)
include_directories(${GSL_INCLUDE_DIRS})

# Find Yaml-cpp
find_package(yaml-cpp REQUIRED)
include_directories(${YAML_CPP_INCLUDE_DIR})

# Find Gazebo
# LOCAL_GAZEBO_DIR can be set to a path with a gazebo-config.cmake
if (LOCAL_GAZEBO_DIR)
    find_package(gazebo 10 REQUIRED CONFIG
            PATHS "${LOCAL_GAZEBO_DIR}"
            NO_DEFAULT_PATH)
    message(WARNING "Using local Gazebo @ ${gazebo_DIR}")
else()
    find_package(gazebo 10 REQUIRED)
endif()
include_directories(${GAZEBO_INCLUDE_DIRS})
link_directories(${GAZEBO_LIBRARY_DIRS})

# Gazebo dependencies
# Find avcodec
pkg_check_modules(libavcodec libavcodec)
if (NOT libavcodec_FOUND)
    BUILD_WARNING ("libavcodec not found. Audio-video capabilities of gazebo are probably disabled.")
else()
    include_directories(${libavcodec_INCLUDE_DIRS})
    link_directories(${libavcodec_LIBRARY_DIRS})
endif ()

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
set(SPEC_DIR "msgs")

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
set(PROTO_OUTPUT_BASE ${CMAKE_CURRENT_BINARY_DIR})


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
        brains/*.cpp
        motors/*.cpp
        sensors/*.cpp
        util/*.cpp
)

# Generate
# _____________________________________________________________________________
# Add the file that registers the body analyzer as a separate library that
# can be used as a world plugin directly.
# Create the library containing the Revolve API

# Generate spec library with the messages
add_library(
        revolve-proto STATIC
        ${PROTO_SRCS} ${PROTO_HDRS}
)
set_target_properties(revolve-proto PROPERTIES LINKER_LANGUAGE CXX)
target_link_libraries(
        revolve-proto
        ${PROTOBUF_LIBRARIES}
)

# Create Revolve bundle plugin
add_library(
        revolve-gazebo
        ${REVOLVE_GZ_SRC}
)

target_link_libraries(
        revolve-gazebo
        ${GAZEBO_LIBRARIES}
        ${Boost_LIBRARIES}
        ${GSL_LIBRARIES}
        ${YAML_CPP_LIBRARIES}
        ${NLOpt_LIBRARIES}
)

target_compile_definitions(
        revolve-gazebo
        PUBLIC ${LIMBO_DEFINES}
)

# Create World plugin
add_library(
        WorldControlPlugin SHARED
        plugin/WorldController.cpp
        plugin/register_world_plugin.cpp
)
target_link_libraries(
        WorldControlPlugin
        revolve-gazebo
        revolve-proto
        ${GAZEBO_LIBRARIES}
)

# Create Analyzer plugin
add_library(
        AnalyzerPlugin SHARED
        plugin/BodyAnalyzer.cpp
        plugin/register_analyzer_plugin.cpp
)
target_link_libraries(
        AnalyzerPlugin
        revolve-gazebo
        revolve-proto
        ${GAZEBO_LIBRARIES}
)

# Create Torus World plugin
add_library(TorusWorldPlugin SHARED
        plugin/TorusWorld.cpp
        plugin/register_torus_world_plugin.cpp
)
target_link_libraries(TorusWorldPlugin
        revolve-gazebo
        ${GAZEBO_LIBRARIES}
)

# Create Robot plugin
add_library(
        RobotControlPlugin SHARED
        plugin/RobotController.cpp
        plugin/register_robot_plugin.cpp
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
