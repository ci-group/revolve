from __future__ import absolute_import

import asyncio
from . import api


class VREPConnectionError(Exception):
    pass


class VrepConnection:
    def __init__(self, address="127.0.0.1", port=19997):
        self._address = address
        self._port = port
        self._client_id = None

    def connect(self,
                wait_until_connected=True,
                do_not_reconnect_once_disconnected=True,
                time_out_in_ms=5000,
                comm_thread_cycle_in_ms=5):
        # just in case, close all opened connections
        # api.simxFinish(-1)

        # Connect
        # print("address:{}".format(self._address))
        # print("port:{}".format(self._port))
        # print("wait_until_connected:{}".format(wait_until_connected))
        # print("do_not_reconnect_once_disconnected:{}".format(do_not_reconnect_once_disconnected))
        # print("time_out_in_ms:{}".format(time_out_in_ms))
        # print("comm_thread_cycle_in_ms:{}".format(comm_thread_cycle_in_ms))
        print("VREP connection started...")
        self._client_id = api.simxStart(self._address,
                                        self._port,
                                        wait_until_connected,
                                        do_not_reconnect_once_disconnected,
                                        time_out_in_ms,
                                        comm_thread_cycle_in_ms)

        if self._client_id == -1:
            raise VREPConnectionError("Error starting connection to vrep, clientID = {}".format(self._client_id))

        print("VREP connection successful")
        return self

    def close(self):
        api.simxFinish(self._client_id)

    def pause(self, pause):
        if pause:
            ret = api.simxPauseSimulation(self._client_id, api.simx_opmode_blocking)
        else:
            ret = api.simxStartSimulation(self._client_id, api.simx_opmode_blocking)
        api.unwrap_vrep(ret)

    def reset_world(self):
        api.unwrap_vrep(
            api.simxStopSimulation(self._client_id, api.simx_opmode_blocking)
        )

    def remove_model(self, name):
        #TODO translate name to handle or take handle as input
        api.unwrap_vrep(
            api.simxRemoveModel(self._client_id, name, api.simx_opmode_oneshot)
        )

    def create_dummy(self):
        """

        :return: dummy handle
        """
        return api.unwrap_vrep(
            api.simxCreateDummy(self._client_id, size=0, color=None, operationMode=api.simx_opmode_blocking)
        )

    def load_scene(self, scene_file):
        print("loading scene file: {}".format(scene_file))
        api.unwrap_vrep(
            # 1 means load the file from the client (Revolve) side
            api.simxLoadScene(self._client_id, scene_file, 1, api.simx_opmode_blocking)
        )

    def call_script_function(self, function_name,
                             input_ints=[], input_floats=[], input_strings=[], input_buffer=bytearray()):

        return api.unwrap_vrep(
            api.simxCallScriptFunction(clientID=self._client_id,
                                       scriptDescription='RevolveRemote',
                                       options=api.sim_scripttype_childscript,
                                       functionName=function_name,
                                       inputInts=input_ints,
                                       inputFloats=input_floats,
                                       inputStrings=input_strings,
                                       inputBuffer=input_buffer,
                                       operationMode=api.simx_opmode_blocking)
        )
