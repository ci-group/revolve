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
    robots = listdir('data')
    robots.remove('.DS_Store')

    battery_path = 'data/'
    output_path = '../../../../output/cpg_bo/'

    for robot in robots:



        battery_info = [f for f in listdir(battery_path + robot) if f.endswith('.txt')]

        for file_name in battery_info:
            global_time = []
            watts_used = []
            current_charge = []
            temp_w = []
            temp_c = []
            temp_diff = []
            i = 1
            with open(battery_path + robot + '/' + file_name, 'r') as file:
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

            df = pd.DataFrame({'global time':global_time, 'watts used':watts_used, 'current charge':current_charge})
            print(df.quantile([.1, .25, .5, .75], axis = 1))
            quit(0)


        num_info = listdir(output_path + robot)
        num_info.remove('.DS_Store')
        for num in num_info:
            with open(output_path + robot + '/' + num + '/speed.txt', 'r') as file:
                speed = []
                for line in file:
                    data = line.strip('\n')
                    speed.append(float(data))





if __name__ == "__main__":
    main()