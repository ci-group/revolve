cmake_minimum_required(VERSION 3.1.0)

message("Building PIGPIO")

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)

add_library(pigpio SHARED
        pigpio.c
        command.c)
target_link_libraries(pigpio
        PUBLIC Threads::Threads)

add_library(pigpio_if SHARED
        pigpiod_if.c
        command.c)
target_link_libraries(pigpio_if
        PUBLIC Threads::Threads)

add_library(pigpio_if2 SHARED
        pigpiod_if2.c
        command.c)
target_link_libraries(pigpio_if2
        PUBLIC Threads::Threads)

add_executable(x_pigpio
        x_pigpio.c)
target_link_libraries(x_pigpio PUBLIC pigpio)

add_executable(x_pigpiod_if
        x_pigpiod_if.c)
target_link_libraries(x_pigpiod_if
        PUBLIC pigpio_if)

add_executable(x_pigpiod_if2
        x_pigpiod_if2.c)
target_link_libraries(x_pigpiod_if2
        PUBLIC pigpio_if2)

add_executable(pigpiod
        pigpiod.c)
target_link_libraries(pigpiod PUBLIC pigpio)

add_executable(pigs
        pigs.c
        command.c)

add_executable(pig2vcd
        pig2vcd.c)

set(PIGPIO_HEADER_DIR ${CMAKE_CURRENT_SOURCE_DIR} PARENT_SCOPE)

install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        PUBLIC_HEADER DESTINATION include
        FILES_MATCHING PATTERN "pi*.h")

install(TARGETS pigpio pigpio_if pigpio_if2 pig2vcd pigpiod pigs
        RUNTIME DESTINATION bin
        LIBRARY DESTINATION lib)


