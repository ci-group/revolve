# Compile C++ tests
file(GLOB_RECURSE TEST_FILES RELATIVE ${CMAKE_CURRENT_SOURCE_DIR} *.cpp)

# Iterate over all tests found. For each file, declare an executable and add it to the tests list.
set(ALL_TESTS)
foreach (FILE ${TEST_FILES})
    # create executable name
    string(REGEX REPLACE "[./]" "_" NAME ${FILE})
    add_executable(${NAME} ${FILE})
    # Link against lib and boost test
    target_link_libraries(${NAME} revolve ${Boost_UNIT_TEST_FRAMEWORK_LIBRARY})
    # Add tests to CMake
    add_test(NAME ${NAME} COMMAND ${NAME})
endforeach (FILE ${TEST_FILES})

include(CTest)
