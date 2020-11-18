import asyncio
import logging
import sys
import os
import math
import numpy as np

from pyrevolve import parser
from pyrevolve.custom_logging import logger
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.SDF.math import Vector3
from pyrevolve.revolve_bot.revolve_module import Orientation
from pyrevolve.tol.manage import World
from pyrevolve.util.supervisor.supervisor_multi import DynamicSimSupervisor
from pyrevolve.evolution import fitness


def rotation(robot_manager, _robot, factor_orien_ds: float = 0.0):
    # TODO move to measurements?
    orientations: float = 0.0
    delta_orientations: float = 0.0

    assert len(robot_manager._orientations) == len(robot_manager._positions)

    fitnesses = [0.]
    choices = ['None']
    i = 0

    for i in range(1, len(robot_manager._orientations)):
        rot_i_1 = robot_manager._orientations[i - 1]
        rot_i = robot_manager._orientations[i]

        angle_i: float = rot_i[2]  # roll / pitch / yaw
        angle_i_1: float = rot_i_1[2]  # roll / pitch / yaw
        pi_2: float = math.pi / 2.0

        if angle_i_1 > pi_2 and angle_i < - pi_2:  # rotating left
            choice = 'A'
            delta_orientations = (2.0 * math.pi + angle_i - angle_i_1) #% (math.pi * 2.0)
        elif (angle_i_1 < - pi_2) and (angle_i > pi_2):
            choice = 'B'
            delta_orientations = - (2.0 * math.pi - angle_i + angle_i_1) #% (math.pi * 2.0)
        else:
            choice = 'C'
            delta_orientations = angle_i - angle_i_1
        #print(f"{choice} {i}\t{delta_orientations:2.0f}\t= {angle_i:2.0f} - {angle_i_1:2.0f}")
        i += 1
        orientations += delta_orientations
        fitnesses.append(orientations)
        choices.append(choice)

    fitnesses = np.array(fitnesses)
    fitnesses -= factor_orien_ds * robot_manager._dist
    return (fitnesses, choices)


def panoramic_rotation(robot_manager, robot: RevolveBot, vertical_angle_limit: float = math.pi/4):
    total_angle = 0.0
    total_angles = [0.]
    vertical_limit = math.sin(vertical_angle_limit)

    # decide which orientation to choose, [0] is correct because the "grace time" values are discarded by the deques
    if len(robot_manager._orientation_vecs) == 0:
        return total_angles

    # Chose orientation base on the
    chosen_orientation = None
    min_z = 1.0
    for orientation, vec in robot_manager._orientation_vecs[0].items():
        z = abs(vec.z)
        if z < min_z:
            chosen_orientation = orientation
            min_z = z
    print(f"Chosen orientation for robot {robot.id} is {chosen_orientation}")

    vec_list = [vecs[chosen_orientation] for vecs in robot_manager._orientation_vecs]

    for i in range(1, len(robot_manager._orientation_vecs)):
        # from: https://code-examples.net/en/q/d6a4f5
        # more info: https://en.wikipedia.org/wiki/Atan2
        # Just like the dot product is proportional to the cosine of the angle,
        # the determinant is proportional to its sine. So you can compute the angle like this:
        #
        # dot = x1*x2 + y1*y2      # dot product between [x1, y1] and [x2, y2]
        # det = x1*y2 - y1*x2      # determinant
        # angle = atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)
        #
        # The function atan2(y,x) (from "2-argument arctangent") is defined as the angle in the Euclidean plane,
        # given in radians, between the positive x axis and the ray to the point (x, y) ≠ (0, 0).

        # u = prev vector
        # v = curr vector
        u: Vector3 = vec_list[i-1]
        v: Vector3 = vec_list[i]

        # if vector is too vertical, fail the fitness
        # (assuming these are unit vectors)
        if abs(u.z) > vertical_limit:
            while len(total_angles) < len(robot_manager._orientations):
                total_angles.append(total_angles[-1])
            return total_angles

        dot = u.x*v.x + u.y*v.y       # dot product between [x1, y1] and [x2, y2]
        det = u.x*v.y - u.y*v.x       # determinant
        delta = math.atan2(det, dot)  # atan2(y, x) or atan2(sin, cos)

        total_angle += delta
        total_angles.append(total_angle)

    return total_angles


async def test_robot_run(robot_file_path: str):
    log = logger.create_logger('experiment', handlers=[
        logging.StreamHandler(sys.stdout),
    ])

    # Set debug level to DEBUG
    log.setLevel(logging.DEBUG)

    # Parse command line / file input arguments
    settings = parser.parse_args()

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
            status = 'dead' if robot_manager.dead else 'alive'
            print(f"Robot fitness ({status}) is \n"
                  f" OLD:     {fitness.online_old_revolve(robot_manager)}\n"
                  f" DISPLAC: {fitness.displacement(robot_manager, robot)}\n"
                  f" DIS_VEL: {fitness.displacement_velocity(robot_manager, robot)}")

            await asyncio.sleep(1.0)
