# CMake Required Version
cmake_minimum_required (VERSION 2.8.12)

# Project Name
project (Revolve)

# CMake flag to help local projects find the build dir
if (${LOCAL_BUILD_DIR})
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

#### Protobuf ####
# This part is currently a mess, but it works for what I need it to
# (which is have includes that work in this project and in the other
#  project I'm working on simultaneously). I might rework it later.
# Get protobuf library
find_package(Protobuf REQUIRED)

# Directory where the .proto file resides
set(SPEC_DIR "${CMAKE_SOURCE_DIR}/revolve/msgs")

include_directories(${CMAKE_SOURCE_DIR} ${PROTOBUF_INCLUDE_DIRS})
file(GLOB_RECURSE REVOLVE_PROTO ${SPEC_DIR}/*.proto)

# Do the protobuf generation by hand for more flexibility. I'm generating
# the files in a subdirectory such that it can potentially be added to
# the include path for work-in-progress projects I co-develop with
# this.
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
foreach(FIL ${REVOLVE_PROTO})
    get_filename_component(ABS_FIL ${FIL} ABSOLUTE)
    get_filename_component(FIL_WE ${FIL} NAME_WE)

    list(APPEND PROTO_SRCS "${PROTO_OUTPUT_BASE}/revolve/msgs/${FIL_WE}.pb.cc")
    list(APPEND PROTO_HDRS "${PROTO_OUTPUT_BASE}/revolve/msgs/${FIL_WE}.pb.h")

    add_custom_command(
      OUTPUT "${PROTO_OUTPUT_BASE}/revolve/msgs/${FIL_WE}.pb.cc"
             "${PROTO_OUTPUT_BASE}/revolve/msgs/${FIL_WE}.pb.h"
      COMMAND  ${PROTOBUF_PROTOC_EXECUTABLE}
      ARGS -I ${SPEC_DIR} --cpp_out  ${PROTO_OUTPUT_BASE}/revolve/msgs ${ABS_FIL}
      DEPENDS ${ABS_FIL}
      COMMENT "Running C++ protocol buffer compiler on ${FIL}"
      VERBATIM )
endforeach()

# Tell the compiler these files were generated
set_source_files_properties(${PROTO_SRCS} ${PROTO_HDRS} PROPERTIES GENERATED TRUE)

# Generate spec library with the messages
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
	 revolve/gazebo/plugin/WorldController.cpp
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



