file(GLOB_RECURSE
        CONTROLLER_SRCS
        controller/*.cpp
        controller/actuators/*.cpp
        controller/sensors/*.cpp
)
file(GLOB_RECURSE
        LEARNER_SRCS
        learner/*.cpp
)

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


add_library(revolve-controllers SHARED ${CONTROLLER_SRCS})
add_library(revolve-learners SHARED ${LEARNER_SRCS})

#target_link_libraries(revolve-controllers
#        PUBLIC
#
#    )
