cmake_minimum_required(VERSION 2.8.12)

project(revolve)

if (BUILD_RASPBERRY)
    add_subdirectory(thirdparty/PIGPIO)
endif()

add_subdirectory(cpprevolve)