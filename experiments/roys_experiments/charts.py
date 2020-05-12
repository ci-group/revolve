import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from os import listdir
from scipy.optimize import curve_fit
import pandas as pd

from scipy.ndimage.filters import gaussian_filter1d


def draw_graph(title, xlabel, x, ylabel, y, avg = False):
    plt.title(title)
    plt.plot(x, y)
    plt.ylabel(ylabel)
    plt.xlabel(xlabel)
    if avg:
        plt.plot(x, gaussian_filter1d(y, sigma=3))
    plt.show()


def draw_both_gaussian(y1, y2, title = ''):

    plt.subplot(2, 1, 1)
    if title == '':
        plt.title('gaussian filter of average speed and energy used per iterations')
    else:
        plt.title(title)
    plt.ylabel('energy')
    plt.plot(range(1,121), y1, label='energy')
    plt.plot(range(1,121), gaussian_filter1d(y1, sigma=3), label='energy')

    plt.subplot(2, 1, 2)
    plt.ylabel('speed')
    plt.xlabel('iteration')
    plt.plot(range(1,121), y2, label='energy')
    plt.plot(range(1,121), gaussian_filter1d(y2, sigma=3), label='speed')
    plt.show()


def main():
    # matplotlib.use('MacOSX')
    output_path = '../../../../output/cpg_bo/'

    robots = listdir(output_path)
    robots.remove('.DS_Store')


    all_robot_battery_avg = None
    all_robot_speed_avg = None

    for robot in robots:
        if '_' in robot and 'main' not in robot:
            robot_battery_avg = None
            robot_speed_avg = None

            time_info = listdir(output_path + robot)

            for time in time_info:
                global_time = []
                watts_used = []
                current_charge = []
                temp_w = []
                temp_c = []
                temp_diff = []
                i = 1
                #   VVV   battery file   VVV
                with open(output_path + robot + '/' + time + '/battery.txt', 'r') as file:
                    for line in file:
                        data = line.strip('\n').split(' ')
                        global_time.append(float(data[0]))
                        watts_used.append(float(data[1]))
                        current_charge.append(float(data[2]))

                        temp_w.append(float(data[1]))
                        temp_c.append(float(data[2]))

                        if float(data[0]) > i * 60:
                            temp_diff.append(temp_c[0]-temp_c[-1])
                            i += 1
                            temp_c.clear()
                            temp_w.clear()

                    # draw_graph('energy used per iteration for ' + robot + '\n iteration: ' + file_name,
                    #            'iteration', range(1, 121), 'total energy used', temp_diff)

                    if robot_battery_avg is None:
                        robot_battery_avg = np.array(temp_diff)
                    else:
                        robot_battery_avg += np.array(temp_diff)

                #   VVV   speed file   VVV
                with open(output_path + robot + '/' + time + '/speed.txt', 'r') as file:
                    speed = []
                    for line in file:
                        data = line.strip('\n')
                        speed.append(float(data))

                    # draw_graph('speed for ' + robot + '\n iteration: ' + num, 'iteration', range(1,121), 'speed', speed)

                    if robot_speed_avg is None:
                        robot_speed_avg = np.array(speed)
                    else:
                        robot_speed_avg += np.array(speed)
            robot_battery_avg /= 10
            # draw_graph('energy used per iteration for ' + robot + '\n average of all iterations ',
            #            'iteration', range(1, 121), 'total energy used', robot_battery_avg)


            robot_speed_avg /= 10
            # draw_graph('speed for ' + robot + '\n average of all iterations ', 'iteration', range(1,121), 'speed', robot_speed_avg)

            # draw_both_gaussian(robot_battery_avg, robot_speed_avg, 'Robot: ' + robot)

            if all_robot_battery_avg is None:
                all_robot_battery_avg = np.array(robot_battery_avg)
            else:
                all_robot_battery_avg += np.array(robot_battery_avg)

            if all_robot_speed_avg is None:
                all_robot_speed_avg = np.array(robot_speed_avg)
            else:
                all_robot_speed_avg += np.array(robot_speed_avg)

    all_robot_speed_avg /= 10
    all_robot_battery_avg /= 10

    draw_graph('average speed for all robots per iteration', 'iterations', range(1, 121), 'average speed', all_robot_speed_avg, True)

    draw_graph('average energy used for all robots per iteration', 'iteration', range(1, 121), 'average energy used', all_robot_battery_avg, True)

    draw_both_gaussian(all_robot_battery_avg, all_robot_speed_avg)

    ratio = []
    for i in range(len(all_robot_speed_avg)):
        ratio.append(all_robot_speed_avg[i]/all_robot_battery_avg[i])

    draw_graph('ratio of average of all speed / average of all energy', 'iteration', range(1, 121), 'speed/energy', ratio, True)









if __name__ == "__main__":
    main()