# CMake Required Version
cmake_minimum_required (VERSION 2.8.12)

# Project Name
project (Revolve)

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
set(SPEC_DIR "${CMAKE_SOURCE_DIR}/../spec")

include_directories(${CMAKE_SOURCE_DIR} ${PROTOBUF_INCLUDE_DIRS})
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
	 revolve/gazebo/*.cpp
)

add_library(rvgzmodelcontrol SHARED ${REVOLVE_GZ_SRC})
target_link_libraries(rvgzmodelcontrol ${GAZEBO_LIBRARIES} ${Boost_LIBRARIES})



