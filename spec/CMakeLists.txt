# CMake Required Version
cmake_minimum_required (VERSION 2.8)

# Project Name
project (Revolve)
find_package(Protobuf REQUIRED)

include_directories(${CMAKE_SOURCE_DIR} ${PROTOBUF_INCLUDE_DIRS})

file (GLOB_RECURSE
     TOL_PROTO
     *.proto
     )

include_directories(${CMAKE_CURRENT_BINARY_DIR})
PROTOBUF_GENERATE_CPP(PROTO_SRCS PROTO_HDRS ${TOL_PROTO})

# Generate spec library
add_library(tol-spec ${PROTO_SRCS} )
target_link_libraries(tol-spec ${PROTOBUF_LIBRARIES})

