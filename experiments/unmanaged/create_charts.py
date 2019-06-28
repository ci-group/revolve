#!/usr/bin/env python3
import os
import sys
import dateutil.parser
import yaml
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from pyrevolve.revolve_bot import RevolveBot


def read_robot(file: str):
    bot = RevolveBot()
    bot.load_file(file)
    return bot


def read_log(filename: str):
    with open(filename) as file:
        log = file.readlines()

    class LogLine:
        def __init__(self, line):
            self.time = dateutil.parser.parse(line[1:24])
            self.type = line[37:41]
            self.text = line[46:]
            self.event_type = 'NEW' if self.text[0:3] == 'LOW' else 'MATE'

        def __repr__(self):
            return f'{self.time} {self.type}\t{self.event_type}'

    def parseline(line):
        return LogLine(line.strip())

    return [parseline(line) for line in log]


def read_robots(folder_name: str):
    robots = {}
    phenotype_folder = os.path.join(folder_name, 'phenotypes')

    class RobotLog:
        def __init__(self, pheno_filename):
            self.robot = RevolveBot()
            self.robot.load_file(os.path.join(phenotype_folder, pheno_filename))
            assert(f'{self.robot.id}.yaml' == pheno_filename)
            with open(os.path.join(folder_name, f'life_{pheno_filename}')) as life_file:
                self.life = yaml.safe_load(life_file)
                birth = self.life['starting_time']
                age = self.life['age']
                self.life['death'] = None if age == 0 else birth + age
                del self.life['avg_orientation']
                del self.life['avg_pos']
                del self.life['charge']
                self.life['birth_reason'] = 'MATE'

        def __repr__(self):
            return f'{self.robot}:{self.life}'

    for pheno_file in os.listdir(phenotype_folder):
        r = RobotLog(pheno_file)
        robots[r.robot.id] = r

    return robots


def read_data(folder_name: str):
    assert(os.path.isdir(folder_name))
    assert(os.path.exists(os.path.join(folder_name, 'experiment_manager.log')))

    return {
        'log': read_log(os.path.join(folder_name, 'experiment_manager.log')),
        'robots': read_robots(folder_name),
    }


def draw_chart(folder_name: str, ax):
    data = read_data(folder_name)
    # print(f'{data}')
    for logline in data['log']:
        # print(f'{logline}')
        if logline.event_type == 'NEW':
            robot_id = logline.text[41:].split('(')[0]
            robot_id = robot_id[11:]
            data['robots'][robot_id].life['birth_reason'] = 'NEW'
            # print(f'{logline.event_type} => {robot_id}')

    robot_points = []
    robot_points_new = []
    robot_points_mate = []
    robot_points_death = []
    robot_points_new_pop = []
    robot_points_mate_pop = []
    robot_points_death_pop = []

    for robot_id in data['robots']:
        robot_log = data['robots'][robot_id]
        # print(f'{robot_log}')
        life = robot_log.life
        birth = life['starting_time']
        age = life['age']
        if life['birth_reason'] == 'NEW':
            robot_points.append(('NEW', birth))
        else:
            robot_points.append(('MATE', birth))
        if life['death'] is not None:
            robot_points.append(('DEATH', life['death']))

    print(f"Drawing {len(data['robots'])} robots, global time TODO")

    robot_points.sort(key=lambda e: e[1])
    pop_size = 0
    for robot_point in robot_points:
        event = robot_point[0]
        time = robot_point[1]
        if event == 'NEW':
            pop_size += 1
            robot_points_new.append(time)
            robot_points_new_pop.append(pop_size)
        elif event == 'MATE':
            pop_size += 1
            robot_points_mate.append(time)
            robot_points_mate_pop.append(pop_size)
        elif event == 'DEATH':
            pop_size -= 1
            robot_points_death.append(time)
            robot_points_death_pop.append(pop_size)
        else:
            raise RuntimeError("WAT?")

    return robot_points_new, robot_points_new_pop, \
           robot_points_mate, robot_points_mate_pop, \
           robot_points_death, robot_points_death_pop


if __name__ == '__main__':
    folder_name = sys.argv[1]

    matplotlib.use('Qt5Agg')
    # matplotlib.use('GTK3Cairo')
    # matplotlib.use('GTK3Agg')
    fig, ax = plt.subplots()
    plt.ion()

    robot_points_new, robot_points_new_pop, \
    robot_points_mate, robot_points_mate_pop, \
    robot_points_death, robot_points_death_pop = draw_chart(folder_name, ax)

    new_scatter = ax.scatter(x=robot_points_new, y=robot_points_new_pop, label='new')
    mate_scatter = ax.scatter(x=robot_points_mate, y=robot_points_mate_pop, label='mate')
    death_scatter = ax.scatter(x=robot_points_death, y=robot_points_death_pop, label='death')
    ax.legend()
    plt.draw()
    plt.pause(0.01)

    def update_data(dataset, points, points_pop):
        assert(len(points) == len(points_pop))
        if len(points) == 0:
            return
        new_data = np.matrix([[x, y] for x, y in zip(points, points_pop)])
        dataset.set_offsets(new_data)

    while True:
        robot_points_new, robot_points_new_pop, \
        robot_points_mate, robot_points_mate_pop, \
        robot_points_death, robot_points_death_pop = draw_chart(folder_name, ax)

        update_data(new_scatter, robot_points_new, robot_points_new_pop)
        update_data(mate_scatter, robot_points_mate, robot_points_mate_pop)
        update_data(death_scatter, robot_points_death, robot_points_death_pop)


        plt.draw()
        plt.pause(2)

    #
    # # Example: loops monitoring events forever.
    # #
    # import pyinotify
    #
    # # Instanciate a new WatchManager (will be used to store watches).
    # wm = pyinotify.WatchManager()
    # # Associate this WatchManager with a Notifier (will be used to report and
    # # process events).
    # notifier = pyinotify.Notifier(wm)
    # # Add a new watch on /tmp for ALL_EVENTS.
    # wm.add_watch(os.path.join(folder_name, 'experiment_manager.log'), pyinotify.ALL_EVENTS)
    # # Loop forever and handle events.
    # notifier.loop()
    #
