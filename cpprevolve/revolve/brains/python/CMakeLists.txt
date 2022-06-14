cmake_minimum_required(VERSION 3.15)
set(CMAKE_CXX_STANDARD 17)

set(SOURCE_FILES
        bindings.cpp
        PyDifferentialCPG.cpp
        )
set(HEADER_FILES
        PyActuator.h
        PyController.h
        PyDifferentialCPG.h
        PySensor.h
        )

if(SKBUILD)
    # Scikit-Build does not add your site-packages to the search path automatically,
    # so we need to add it _or_ the pybind11 specific directory here.
    execute_process(
            COMMAND
            "${PYTHON_EXECUTABLE}" -c
            "import pybind11; print(pybind11.get_cmake_dir())"
            OUTPUT_VARIABLE _tmp_dir
            OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ECHO STDOUT)
    list(APPEND CMAKE_PREFIX_PATH "${_tmp_dir}")
endif()

# Find python version before pybind11, it will pick up the same version
find_package(Python COMPONENTS Interpreter Development)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(revolvebrains
        ${SOURCE_FILES} ${HEADER_FILES})

target_link_libraries(revolvebrains
        PRIVATE revolve-controllers
        PRIVATE revolve-learners)

target_compile_definitions(revolvebrains PRIVATE VERSION_INFO=${PROJECT_VERSION})
set_target_properties(revolvebrains
        PROPERTIES
        #ARCHIVE_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/pyrevolve/revolve_bot/brain/controller"
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/pyrevolve/revolve_bot/brain/controller"
        #RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/pyrevolve/revolve_bot/brain/controller"
        )

install(TARGETS revolvebrains DESTINATION .)
