cmake_minimum_required(VERSION 2.8.12)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_CURRENT_SOURCE_DIR}/cmake)

# enable_testing() needed on top-level CMakeLists.txt
enable_testing()

# Create target for generating documentation
add_custom_target(doc)
add_dependencies(doc docRevolve)

add_subdirectory(Revolve)
add_subdirectory(tol-revolve)