from . import *


class VrepApiError(Exception):
    def __init__(self, ret_code):
        if ret_code == simx_return_ok:
            raise ValueError("Invalid VrepApiError error code")
        elif ret_code == simx_return_novalue_flag:  # 1
            message = "There is no command reply in the input buffer. This should not always be considered as an " \
                      "error, depending on the selected operation mode "
        elif ret_code == simx_return_timeout_flag:  # 2
            message = "The function timed out (probably the network is down or too slow)"
        elif ret_code == simx_return_illegal_opmode_flag:  # 4
            message = "The specified operation mode is not supported for the given function"
        elif ret_code == simx_return_remote_error_flag:  # 8
            message = "The function caused an error on the server side (e.g. an invalid handle was specified)"
        elif ret_code == simx_return_split_progress_flag:  # 16
            message = "The communication thread is still processing previous split command of the same type"
        elif ret_code == simx_return_local_error_flag:  # 32
            message = "The function caused an error on the client side"
        elif ret_code == simx_return_initialize_error_flag:  # 64
            message = "simxStart was not yet called"
        else:
            message = "Unknown error code {}".format(ret_code)

        super().__init__(message)


def unwrap_vrep(result):
    if type(result) is tuple:
        ret_code = result[0]
        result = result[1:]
        if len(result) == 1:
            result = result[0]

        if ret_code > 0:
            raise VrepApiError(ret_code)

        return result
