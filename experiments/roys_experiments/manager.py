#!/usr/bin/env python3
import os
import sys
import asyncio

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
sys.path.append(newpath)

from pygazebo.pygazebo import DisconnectError

from pyrevolve import revolve_bot
from pyrevolve import parser
from pyrevolve.SDF.math import Vector3
from pyrevolve.tol.manage import World
from pyrevolve.evolution import fitness
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor


async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments
    settings = parser.parse_args()

    # Load a robot from yaml
    robot = revolve_bot.RevolveBot()
    robot.load_file("experiments/bo_learner/yaml/spider9.yaml")
    robot.update_substrate()
    robot.save_file("./spider.sdf", conf_type='sdf')


    # Start Simulator
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

    # Connect to the simulator and pause
    world = await World.create(settings)
    await world.pause(True)

    await (await world.delete_model(robot.id))
    await asyncio.sleep(2.5)

    # Insert the robot in the simulator
    insert_future = await world.insert_robot(robot, Vector3(0, 0, 0.25))
    robot_manager = await insert_future

    # Resume simulation
    await world.pause(False)

    # Start a run loop to do some stuff
    while True:
        # Print robot fitness every second
        # fitness_=fitness(robot_manager)
        # print(f"Robot fitness is {fitness_}")
        await asyncio.sleep(1.0)


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
        print("Got CtrlC, shutting down.")


if __name__ == '__main__':
    print("STARTING")
    main()
    print("FINISHED")
