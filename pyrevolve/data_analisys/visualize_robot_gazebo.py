import argparse
import asyncio
import logging
import os
from typing import AnyStr

from pyrevolve.SDF.math import Vector3
from pyrevolve.data_analisys.visualize_robot import panoramic_rotation
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.spec import Orientation
from pyrevolve.evolution import fitness
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor


async def test_robot_run_gazebo(robot_file_path: AnyStr, log: logging.Logger, settings: argparse.Namespace):
    world: AnyStr = settings.world
    if settings.record:
        # world = "plane.recording.world"
        _world = world.split('.')  # type: List[AnyStr]
        _world.insert(-1, 'recording')
        world = '.'.join(_world)

    # Start Simulator
    if settings.simulator_cmd != 'debug':
        simulator_supervisor = DynamicSimSupervisor(
            world_file=world,
            simulator_cmd=settings.simulator_cmd,
            simulator_args=["--verbose"],
            plugins_dir_path=os.path.join('.', 'build', 'lib'),
            models_dir_path=os.path.join('.', 'models'),
            simulator_name='gazebo'
        )
        await simulator_supervisor.launch_simulator(port=settings.port_start)
        await asyncio.sleep(0.1)

    # Connect to the simulator and pause
    connection = await World.create(settings, world_address=('127.0.0.1', settings.port_start))
    await asyncio.sleep(1)

    # init finished

    robot = RevolveBot(_id=settings.test_robot)
    robot.load_file(robot_file_path, conf_type='yaml')
    robot.update_substrate()
    robot.save_file(f'{robot_file_path}.sdf', conf_type='sdf')

    await connection.pause(True)
    robot_manager = await connection.insert_robot(robot, Vector3(0, 0, 0.25), life_timeout=None)
    await asyncio.sleep(1.0)

    if settings.plot_test_robot:
        import matplotlib.pyplot as plt
        import matplotlib
        gui_env = ['TKAgg', 'GTK3Agg', 'Qt5Agg', 'Qt4Agg', 'WXAgg']
        for gui in gui_env:
            try:
                print("testing", gui)
                matplotlib.use(gui, warn=False, force=True)
                from matplotlib import pyplot as plt
                break
            except Exception as e:
                print(e)
                continue
        print("Using:", matplotlib.get_backend())
        plt.ion()
        fig, ax1 = plt.subplots(1, 1)
        SIZE = 300

        line10, = ax1.plot([0 for i in range(SIZE)], [0 for i in range(SIZE)], '-', label='x')
        line11, = ax1.plot([0 for i in range(SIZE)], [0 for i in range(SIZE)], '-', label='y')
        line12, = ax1.plot([0 for i in range(SIZE)], [0 for i in range(SIZE)], '-', label='z')
        line13, = ax1.plot([0 for i in range(SIZE)], [0 for i in range(SIZE)], '-', label='fitness')
        # line20, = ax2.plot([0 for i in range(SIZE)], [0 for i in range(SIZE)], '-', label='x')
        # line21, = ax2.plot([0 for i in range(SIZE)], [0 for i in range(SIZE)], '-', label='y')
        # line22, = ax2.plot([0 for i in range(SIZE)], [0 for i in range(SIZE)], '-', label='z')
        # line23, = ax2.plot([0 for i in range(SIZE)], [0 for i in range(SIZE)], '-', label='fitness')
        ax1.legend()
        # ax2.legend()
        fig.show()
        EPS = 0.1

        def update(line, ax, x, y):
            # print(f'x={x}')
            # print(f'y={y}')
            # line.set_data(x, y)
            line.set_ydata(y)
            line.set_xdata(x)
            miny = min(min(y)-EPS, ax.get_ylim()[0])
            maxy = max(max(y)+EPS, ax.get_ylim()[1])
            ax.set_xlim(min(x)-EPS, max(x)+EPS)
            ax.set_ylim(miny, maxy)

        while True:
            await asyncio.sleep(0.1)
            times = [float(t) for t in robot_manager._times]
            steps = [i for i in range(len(times))]
            vecs = [vec[Orientation.FORWARD] for vec in robot_manager._orientation_vecs]
            xs = [float(v.x) for v in vecs]
            ys = [float(v.y) for v in vecs]
            zs = [float(v.z) for v in vecs]
            # fitnesses, _ = rotation(robot_manager, robot)
            fitnesses = panoramic_rotation(robot_manager, robot)
            #fitness.panoramic_rotation(robot_manager, robot)
            if len(times) < 2:
                continue
            assert len(times) == len(xs)
            update(line10, ax1, times, xs)
            update(line11, ax1, times, ys)
            update(line12, ax1, times, zs)
            update(line13, ax1, times, fitnesses)
            # update(line20, ax2, steps, xs)
            # update(line21, ax2, steps, ys)
            # update(line22, ax2, steps, zs)
            # update(line23, ax2, steps, fitnesses)
            fig.canvas.draw()
            fig.canvas.flush_events()

    else:
        # Start the main life loop
        while True:
            # Print robot fitness every second
            if not settings.record:
                status = 'dead' if robot_manager.dead else 'alive'
                print(f"Robot fitness ({status}) is \n"
                      f" OLD:     {fitness.online_old_revolve(robot_manager)}\n"
                      f" DISPLAC: {fitness.displacement(robot_manager, robot)}\n"
                      f" DIS_VEL: {fitness.displacement_velocity(robot_manager, robot)}")

            await asyncio.sleep(1.0)
