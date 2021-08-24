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

# Find Eigen3 - A lightweight C++ template library for vector and matrix math
find_package(Eigen3 REQUIRED)

find_package(MultiNEAT REQUIRED)

# Find NLOpt - Non Linear Optimization
pkg_check_modules(NLOpt REQUIRED nlopt>=2.4)

# Find Limbo - LIbrary for Model-Based Optimization
set(LIMBO_DIR ${CMAKE_SOURCE_DIR}/thirdparty/limbo)
set(LIMBO_DEFINES USE_NLOPT)

add_library(revolve-controllers SHARED ${CONTROLLER_SRCS})
add_library(revolve-learners SHARED ${LEARNER_SRCS})

target_include_directories(revolve-controllers
        PUBLIC ${EIGEN3_INCLUDE_DIR}
        PUBLIC ${Boost_INCLUDE_DIRS})

target_include_directories(revolve-learners
        PUBLIC ${Boost_INCLUDE_DIRS}
        PUBLIC ${LIMBO_DIR}/src
        PUBLIC ${NLOpt_INCLUDE_DIRS})

target_include_directories(revolve-learners
        PUBLIC ${NLOpt_LIBRARY_DIRS})

target_link_libraries(revolve-controllers
        MultiNEAT::MultiNEAT)

install(TARGETS revolve-controllers revolve-learners
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib)

if(DEFINED PYTHON_BRAIN_BINDINGS)
    add_subdirectory(python)
endif()
