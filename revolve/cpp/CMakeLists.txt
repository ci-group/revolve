# Initial setups
# _____________________________________________________________________________

# The name of the project
project("Revolve")

# A version number of the project
set(VERSION_MAJOR "0")
set(VERSION_MINOR "1")
set(VERSION_PATCH "0")
set(VERSION ${VERSION_MAJOR}.${VERSION_MINOR}.${VERSION_PATCH})

# CMake useful variables
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")

# This sets the include directory for the reference project. This is the -I flag in gcc.
# All the includes should be in this variable To add new directories to the include path,
# just add them in this list (after a space), or add an include_directories statement in a
# subdirectory's CMakeLists.
include_directories(
        ${PROJECT_SOURCE_DIR}/include
        ${PROJECT_BINARY_DIR}/include   # add the binary tree to the search path so that we will find Version.h
)

# MacOS X needed variables
if (${CMAKE_SYSTEM_NAME} MATCHES "Darwin")
    # adaptable according to individual needs
    set(CMAKE_MACOSX_RPATH ON)
    #    set(CMAKE_SKIP_BUILD_RPATH FALSE)
    #    set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)
    #    set(CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/lib")
    #    set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
endif ()

# Finding dependencies
# _____________________________________________________________________________

include(Common)

# Find the boost lib and headers.
set(Boost_NO_BOOST_CMAKE ON) #  Don't do a find_package in config mode before searching for a regular boost install.
find_package(Boost COMPONENTS REQUIRED
        "program_options"
        "system"
        "unit_test_framework"
        )
include_directories(${Boost_INCLUDE_DIRS})

# Find and include Gazebo
# LOCAL_GAZEBO_DIR can be set to a path with a gazebo-config.cmake
if (LOCAL_GAZEBO_DIR)
    find_package(gazebo 6.5 REQUIRED CONFIG
            PATHS "${LOCAL_GAZEBO_DIR}"
            NO_DEFAULT_PATH)
    message(WARNING "Using local Gazebo @ ${gazebo_DIR}")
else ()
    find_package(gazebo 6.5 REQUIRED)
endif ()
include_directories(${GAZEBO_INCLUDE_DIRS})
include_directories(${GAZEBO_PROTO_INCLUDE})

# Add Gazebo C++ flags (this includes c++11)
list(APPEND CMAKE_CXX_FLAGS "${GAZEBO_CXX_FLAGS}")

# Find protobuf
find_package(Protobuf REQUIRED)
include_directories(${PROTOBUF_INCLUDE_DIRS})

# Source subdirectories
# _____________________________________________________________________________

enable_testing()
add_subdirectory(doc)
add_subdirectory(include)
add_subdirectory(src)
add_subdirectory(test)

# System packaging (RPM, TGZ, ...)
# _____________________________________________________________________________

#include(CPackConfig)

# CMake packaging (so other CMake projects can use this one easily)
# _____________________________________________________________________________

#include(PackageConfigurator)