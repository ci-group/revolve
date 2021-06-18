cmake_minimum_required (VERSION 3.7.0)

project(revolve)

set(CMAKE_CXX_STANDARD 17)

add_library(revolve-utils STATIC
        Address.cpp Address.h
)

set_property(TARGET revolve-utils
        PROPERTY POSITION_INDEPENDENT_CODE ON
)
