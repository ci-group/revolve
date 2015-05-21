# CMake Required Version
cmake_minimum_required (VERSION 2.8.12)

# Project Name
project (Revolve)

# CMake flag to help local projects find the build dir
if (${LOCAL_BUILD_DIR})
    set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../build/lib")
    set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../build/lib")
    set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../build")
    message("Using local build directory.")
endif()

# Pass source dir to preprocessor
add_definitions(-DSOURCE_DIR=${CMAKE_SOURCE_DIR})

# Compiler options
# TODO This currently assumes GCC, add Windows support in due time
add_definitions(-pedantic -Wno-long-long -Wall -Wextra -Wformat=2
                -Wredundant-decls -Wwrite-strings -Wmissing-include-dirs 
                -Wswitch-enum -Wuninitialized 
                -Wswitch-default -Winit-self -Wfloat-equal -fPIC )

# Use C++11
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

# Debug Flags 
set(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -O0 -ggdb3 -DDEBUG")

# Release flags
#set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} -O3 -funroll-loops -finline-functions -fomit-frame-pointer -DNDEBUG")

#### Protobuf spec ####
# Get protobuf library
find_package(Protobuf REQUIRED)

# Directory where the .proto file resides
set(SPEC_DIR "${CMAKE_SOURCE_DIR}/revolve/msgs")

include_directories(${CMAKE_SOURCE_DIR} ${PROTOBUF_INCLUDE_DIRS})

# Include the binary dir since that is where the protobuf files are
# going to be placed.
include_directories(${CMAKE_CURRENT_BINARY_DIR})
file(GLOB_RECURSE REVOLVE_PROTO ${SPEC_DIR}/*.proto)
PROTOBUF_GENERATE_CPP(PROTO_SRCS PROTO_HDRS ${REVOLVE_PROTO})

# Generate spec library
add_library(revolve-spec STATIC ${PROTO_SRCS} )
target_link_libraries(revolve-spec ${PROTOBUF_LIBRARIES})

#### Other sources #######
# Find Boost and add to include dirs
find_package(Boost REQUIRED COMPONENTS system)
include_directories(${Boost_INCLUDE_DIRS})

# Gazebo control plugins
# Find and include Gazebo
include (FindPkgConfig)
if (PKG_CONFIG_FOUND)
  pkg_check_modules(GAZEBO gazebo)
endif()
include_directories(${GAZEBO_INCLUDE_DIRS})

# Plugin CPP files
file(GLOB_RECURSE
	 REVOLVE_GZ_SRC
	 revolve/gazebo/brain/*.cpp
	 revolve/gazebo/motors/*.cpp
	 revolve/gazebo/sensors/*.cpp
	 revolve/gazebo/plugin/BodyAnalyzer.cpp
	 revolve/gazebo/plugin/RobotController.cpp
)

# Create the library containing the Revolve API
add_library(revolve-gazebo ${REVOLVE_GZ_SRC})
target_link_libraries(revolve-gazebo ${GAZEBO_LIBRARIES} ${Boost_LIBRARIES})

# Add the file that registers the body analyzer as a separate library that
# can be used as a world plugin directly.
add_library(revolve-body-analyzer SHARED revolve/gazebo/plugin/register_analyzer.cpp)
target_link_libraries(revolve-body-analyzer revolve-gazebo revolve-spec ${GAZEBO_LIBRARIES})

# Add the analyzer server standalone
add_executable(body-analyzer revolve/gazebo/standalone/body_analyzer_server.cpp)
target_link_libraries(body-analyzer revolve-body-analyzer ${GAZEBO_LIBRARIES} ${Boost_LIBRARIES})

# Install libraries into "lib", header files into "include"
install(
    TARGETS revolve-spec revolve-gazebo
    DESTINATION lib
)

install(
   DIRECTORY revolve
   DESTINATION include
   FILES_MATCHING PATTERN "*.h"
)



