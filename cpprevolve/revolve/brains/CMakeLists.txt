file(GLOB_RECURSE
    CONTROLLER_SRCS
    controller/*.cpp
)
file(GLOB_RECURSE
    LEARNER_SRCS
    learner/*.cpp
)

add_library(revolve-controllers SHARED ${CONTROLLER_SRCS})
add_library(revolve-learners SHARED ${LEARNER_SRCS})
