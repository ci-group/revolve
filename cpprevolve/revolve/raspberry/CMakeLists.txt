message(WARNING "Building Raspberry code")

# Find Yaml-cpp
find_package(yaml-cpp REQUIRED)
include_directories(${YAML_CPP_INCLUDE_DIR})

file(GLOB_RECURSE
        RASPBERRY_SRCS
        *.cpp
        )

add_executable(revolve-raspberry ${RASPBERRY_SRCS})

target_link_libraries(revolve-raspberry
        PUBLIC revolve-controllers
        PUBLIC pigpio_if2
        ${YAML_CPP_LIBRARIES}
)

include_directories(${PIGPIO_HEADER_DIR})

install(TARGETS revolve-raspberry
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib)
