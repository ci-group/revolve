#!/usr/bin/env python3
import asyncio
import os
import sys
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve import parser

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyrevolve.gazebo.manage import WorldManager as World


async def run():
    # Start Simulator
    settings = parser.parse_args()
    if settings.simulator_cmd != 'debug':
        simulator_supervisor = DynamicSimSupervisor(
            world_file=settings.world,
            simulator_cmd=settings.simulator_cmd,
            simulator_args=["--verbose"],
            plugins_dir_path=os.path.join('.', 'build', 'lib'),
            models_dir_path=os.path.join('.', 'models'),
            simulator_name='gazebo'
        )
        await simulator_supervisor.launch_simulator(port=settings.port_start)
        await asyncio.sleep(0.1)

    world = await World.create()
    if world:
        print("Connected to the simulator world.")

    sdf_model = """
    <sdf version ='1.5'>
        <model name ='sphere'>
            <pose>1 0 0 0 0 0</pose>
            <link name ='link'>
                <pose>0 0 .5 0 0 0</pose>
                <collision name ='collision'>
                    <geometry>
                        <sphere>
                            <radius>0.5</radius>
                        </sphere>
                    </geometry>
                </collision>
                <visual name ='visual'>
                    <geometry>
                        <sphere>
                            <radius>0.5</radius>
                        </sphere>
                    </geometry>
                </visual>
            </link>
        </model>
    </sdf>"""

    await world.insert_model(sdf_model)
    await world.pause(True)

    while True:
        await asyncio.sleep(10.0)


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()