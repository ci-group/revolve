#!/usr/bin/env python3
import os
import sys
import asyncio
import importlib

from pygazebo.pygazebo import DisconnectError
from pyrevolve import parser

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def run():
    arguments = parser.parse_args()
    if arguments.test_robot is not None:
        manager = importlib.import_module(arguments.manager).run
        return await manager()

    if arguments.manager is not None:
        # this split will give errors on windows
        manager_lib = os.path.splitext(arguments.manager)[0]
        manager_lib = '.'.join(manager_lib.split('/'))
        manager = importlib.import_module(manager_lib).run
        return await manager()


def main():
    import traceback

    def handler(_loop, context):
        try:
            exc = context['exception']
        except KeyError:
            print(context['message'])
            return

        if isinstance(exc, DisconnectError) \
                or isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            sys.exit(0)

        if isinstance(exc, OSError) and exc.errno == 9:
            print(exc)
            traceback.print_exc()
            return

        traceback.print_exc()
        raise exc

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handler)
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Got CtrlC, shutting down.")


if __name__ == '__main__':
    print("STARTING")
    main()
    print("FINISHED")

