"""
Multi-future function to amend that missing functionality
in Trollius. Code taken mostly from Tornado.
"""
from __future__ import absolute_import
from __future__ import print_function

import sys

from asyncio import Future


def multi_future(children, quiet_exceptions=()):
    """
    Wraps multiple futures in a single future.
    :param quiet_exceptions:
    :param children:
    """
    if isinstance(children, dict):
        keys = list(children.keys())
        children = list(children.values())
    else:
        keys = None
    unfinished_children = set(children)

    future = Future()
    if not children:
        future.set_result({} if keys is not None else [])

    def callback(ft):
        unfinished_children.remove(ft)
        if not unfinished_children:
            result_list = []
            for ft in children:
                try:
                    result_list.append(ft.result())
                except Exception as e:
                    if future.done():
                        if not isinstance(e, quiet_exceptions):
                            print("Multiple exceptions in yield list",
                                  file=sys.stderr)
                    else:
                        future.set_exception(sys.exc_info())
            if not future.done():
                if keys is not None:
                    future.set_result(dict(list(zip(keys, result_list))))
                else:
                    future.set_result(result_list)

    listening = set()
    for f in children:
        if f not in listening:
            listening.add(f)
            f.add_done_callback(callback)

    return future


async def wait_for(coro):
    """
    This function was created to counter the common
    pattern where you do this:

    ```
    fut = yield From(some_func())
    result = yield From(fut)
    ```

    which can instead now be done like this:

    ```
    result = yield From(wait_for(some_func())
    ```

    saving an annoying couple of lines of code
    every time.

    :param coro: A coroutine
    :return:
    """
    fut = await coro
    result = await fut
    return result
