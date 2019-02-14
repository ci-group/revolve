#!/usr/bin/env python3
import asyncio
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pygazebo.pygazebo import DisconnectError

from pyrevolve import parser
from pyrevolve.gazebo.manage import WorldManager as World


async def run():
    print('Hello World from `{}`'.format(rvpath))
    settings = parser.parse_args()

    world = await World.create()
    if world:
        print("Connected to the simulator world.")

    await world.pause(True)

    while True:
        await asyncio.sleep(10.0)


def main():
    def handler(loop, context):
        exc = context['exception']
        if isinstance(exc, DisconnectError) \
                or isinstance(exc, ConnectionResetError):
            print("Got disconnect / connection reset - shutting down.")
            sys.exit(0)
        raise context['exception']

    try:
        loop = asyncio.get_event_loop()
        loop.set_exception_handler(handler)
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print("Got Ctrl+C, shutting down.")


if __name__ == "__main__":
    main()
