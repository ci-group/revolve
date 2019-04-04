#!/usr/bin/env python3
import asyncio
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.join(current_dir, '..', '..')
sys.path.append(rvpath)

from pygazebo.pygazebo import DisconnectError

from pyrevolve.gazebo.manage import WorldManager as World
from pyrevolve.sdfbuilder import Link
from pyrevolve.sdfbuilder import Model
from pyrevolve.sdfbuilder import SDF
from pyrevolve.sdfbuilder.math import Vector3


async def run():
    world = await World.create()
    if world:
        print("Connected to the simulator world.")

    model = Model(
            name='sdf_model',
            static=True,
    )
    model.set_position(position=Vector3(0, 0, 1))
    link = Link('sdf_link')
    link.make_sphere(
            mass=10e10,
            radius=0.5,
    )
    link.make_color(0.7, 0.2, 0.0, 1.0)

    model.add_element(link)
    sdf_model = SDF(elements=[model])

    await world.insert_model(sdf_model)
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
