message(WARNING "Building Raspberry code")

file(GLOB_RECURSE
        RASPBERRY_SRCS
        *.cpp
        )

add_executable(revolve-raspberry ${RASPBERRY_SRCS})

target_link_libraries(revolve-raspberry
        PUBLIC revolve-controllers
        PUBLIC pigpio_if2
)

#target_link_libraries(revolve-controllers
#        PUBLIC
#
#    )
