# Initialise variables
# _____________________________________________________________________________

#set(LIB_HEADERS
#        "${CMAKE_CURRENT_BINARY_DIR}/../include/Revolve/Version.h" # Generated header
#        ../include/revolve/World.h # Normal header
#        )
#
#set(LIB_SOURCES
##        World.cxx
#        )
#
#set(APP_HEADERS
#        )
#
#set(APP_SOURCES
##        main.cxx
#        )

# Generate protobuf static library
# _____________________________________________________________________________

# Find the protobuf import directory for Gazebo. Code from this
# tutorial: http://gazebosim.org/tutorials?tut=custom_messages
set(GAZEBO_PROTOBUF_DIR)
foreach(ITR ${GAZEBO_INCLUDE_DIRS})
    if(ITR MATCHES ".*gazebo-[0-9.]+$")
        set(GAZEBO_PROTO_PATH "${ITR}/gazebo/msgs/proto")
        set(GAZEBO_PROTO_INCLUDE "${ITR}/gazebo/msgs")
    endif()
endforeach()
include_directories(${CMAKE_SOURCE_DIR} ${GAZEBO_PROTO_INCLUDE})

# Directory where the custom .proto files reside within Revolve
set(REVOLVE_PROTO_DIR "${CMAKE_SOURCE_DIR}/revolve/cpp/src/revolve/msgs")

# All protobuf files we need, including the Gazebo ones
file(GLOB_RECURSE REVOLVE_PROTO ${REVOLVE_PROTO_DIR}/*.proto)

# Do the protobuf generation by hand for more flexibility.
# The files are generated in a subdirectory such that it can potentially
# be added to the include path for work-in-progress projects co-developed
# with this one, or new project that extends Revolve.
# Copied most of this code from
# http://stackoverflow.com/q/29346488
# Also see
# https://github.com/Kitware/CMake/blob/master/Modules/FindProtobuf.cmake
if (HEADER_COPY_DIR)
    set(PROTO_OUTPUT_BASE ${HEADER_COPY_DIR})
else()
    set(PROTO_OUTPUT_BASE ${CMAKE_CURRENT_BINARY_DIR})
endif()

# Include the directory where the protobuf files will be placed
include_directories(${PROTO_OUTPUT_BASE})

set(PROTO_SRCS)
set(PROTO_HDRS)
file(MAKE_DIRECTORY ${PROTO_OUTPUT_BASE}/revolve/msgs)
foreach(FIL ${REVOLVE_PROTO})
    get_filename_component(ABS_FIL ${FIL} ABSOLUTE)
    get_filename_component(FIL_WE ${FIL} NAME_WE)
    get_filename_component(FILE_DIR ${FIL} DIRECTORY)

    list(APPEND PROTO_SRCS "${PROTO_OUTPUT_BASE}/revolve/msgs/${FIL_WE}.pb.cc")
    list(APPEND PROTO_HDRS "${PROTO_OUTPUT_BASE}/revolve/msgs/${FIL_WE}.pb.h")

    add_custom_command(
            OUTPUT "${PROTO_OUTPUT_BASE}/revolve/msgs/${FIL_WE}.pb.cc"
            "${PROTO_OUTPUT_BASE}/revolve/msgs/${FIL_WE}.pb.h"
            COMMAND  ${PROTOBUF_PROTOC_EXECUTABLE}
            ARGS -I ${FILE_DIR}
            -I ${GAZEBO_PROTO_PATH}
            --cpp_out ${PROTO_OUTPUT_BASE}/revolve/msgs ${ABS_FIL}
            DEPENDS ${ABS_FIL}
            COMMENT "Running C++ protocol buffer compiler on ${FIL}"
            VERBATIM )
endforeach()

# Tell the compiler these files were generated
set_source_files_properties(${PROTO_SRCS} ${PROTO_HDRS} PROPERTIES GENERATED TRUE)

# Generate spec library with the messages
add_library(revolve-spec STATIC ${PROTO_SRCS})
set_target_properties(revolve-spec PROPERTIES LINKER_LANGUAGE CXX)
target_link_libraries(revolve-spec ${PROTOBUF_LIBRARIES})


# Generate Gazebo control plugin
# _____________________________________________________________________________

file(GLOB_RECURSE
        REVOLVE_GAZEBO_SRC
        revolve/gazebo/brain/*.cpp
        revolve/gazebo/actuators/*.cpp
        revolve/gazebo/sensors/*.cpp
        revolve/gazebo/plugin/BodyAnalyzer.cpp
        revolve/gazebo/plugin/RobotController.cpp
        revolve/gazebo/plugin/WorldController.cpp
        )

# Create the library containing the Revolve API
add_library(revolve-gazebo ${REVOLVE_GAZEBO_SRC})
target_link_libraries(revolve-gazebo
        ${GAZEBO_LIBRARIES}
        ${Boost_LIBRARIES}
        revolve-spec
        )

# Generate
# _____________________________________________________________________________
# Add the file that registers the body analyzer as a separate library that
# can be used as a world plugin directly.
add_library(revolve-body-analyzer SHARED revolve/gazebo/plugin/register_analyzer.cpp)
target_link_libraries(revolve-body-analyzer
        ${GAZEBO_LIBRARIES}
        revolve-gazebo
        revolve-spec
        )

# Generate
# _____________________________________________________________________________
# Add the analyzer server standalone
add_executable(body-analyzer revolve/gazebo/standalone/body_analyzer_server.cpp)
target_link_libraries(body-analyzer
        ${GAZEBO_LIBRARIES}
        ${Boost_LIBRARIES}
        revolve-body-analyzer
        )

# Install
# _____________________________________________________________________________
## Says how and where to install software
## Targets:
##   * <prefix>/lib/<libraries>
##   * header location after install: <prefix>/include/<project>/*.h
##   * headers can be included by C++ code `#<project>/Bar.hpp>`
#install(TARGETS ${LIBRARY_NAME} ${APPLICATION_NAME}
#        EXPORT ${PROJECT_NAME}Targets            # for downstream dependencies
#        ARCHIVE DESTINATION lib COMPONENT libs   # static lib
#        RUNTIME DESTINATION bin COMPONENT libs   # binaries
#        LIBRARY DESTINATION lib COMPONENT libs   # shared lib
#        FRAMEWORK DESTINATION bin COMPONENT libs # for mac
#        PUBLIC_HEADER DESTINATION include/${PROJECT_NAME} COMPONENT devel   # headers for mac (note the different component -> different package)
#        INCLUDES DESTINATION include             # headers
#        )