set(VREP_WORLD_PLUGIN_SOURCES
    plugin/register_world_plugin.cpp
)

add_library(v_repExtRevolveWorld SHARED ${VREP_WORLD_PLUGIN_SOURCES})
target_include_directories(v_repExtRevolveWorld PUBLIC "/usr/share/vrep/programming")
set_property(TARGET v_repExtRevolveWorld PROPERTY POSITION_INDEPENDENT_CODE ON)
