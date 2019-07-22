import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from os import listdir
from os.path import isfile, join


from scipy.ndimage.filters import gaussian_filter1d


def nice_chart(col_name, do_log=False, do_exp=False, axs=None, col_normalize=None):
    n = 3
    viridis = matplotlib.cm.get_cmap('viridis', n)
    colormap = viridis(np.linspace(0, 1, n))
    if axs is None:
        fig, axs = plt.subplots(1,1, figsize=(8,8))

    title = col_name
    if col_normalize is not None:
        title = col_name + ' / ' + col_normalize
    if do_log:
        title = title + " (log)"
    elif do_exp:
        title = title + " (exp)"


    axs.set_title(title)

    for_list = [
        (0, 'direct',  direct,  axs, colormap[0]),
        (1, 'lsystem', lsystem, axs, colormap[1]),
        (2, 'cppn',    cppn,    axs, colormap[2]),
    ]

    for i, title, data, ax, color in for_list:
        values = []
        for name,group in data.groupby('gen'):
            line_values = group[col_name]
            if col_normalize is not None:
                line_values = line_values / group[col_normalize]
                ax.set_ylim((0,1))
            if do_log:
                line_values = np.log(line_values)
            elif do_exp:
                line_values = np.exp(line_values)

            values.append([np.average(line_values)] + np.percentile(line_values, [0, 25, 50, 75, 100]).tolist())
        values = pd.DataFrame(data=values, columns=['avg','0','25','50','75','100'])

        x = np.arange(600)
        #ax.set_title(title)
        ax.plot(values['avg'], linewidth=2, color=color, label=title)
        ax.fill_between(x, values['25'], values['75'], alpha=0.4, color=color)

        offset= i*10
        x = np.arange(offset, 599, 60)
        yerr_top = []
        yerr_bottom = []
        yerr_interval = []
        for i in range(len(x)):
            yerr_top.append(values['avg'][x[i]] - values['100'][x[i]])
            yerr_bottom.append(values['0'][x[i]] - values['avg'][x[i]])
            yerr_interval.append(values['avg'][x[i]])
        ax.errorbar(x, yerr_interval, yerr=[yerr_top, yerr_bottom], alpha=0.4, capsize=2, color=color);

    axs.legend(fontsize=12, loc="lower right", bbox_to_anchor=[1, 0],
               ncol=2, shadow=True, fancybox=True)


def average(n, lst):
    res = []
    for i in range(len(lst)//n):
        res.append(sum(lst[i*n:(i+1)*n])/n)
    return res


def draw_graph(name, x, y):
    plt.title('Watts Used Plot ' + name)
    # plt.plot(x, y)
    plt.plot(x, gaussian_filter1d(y, sigma=100))
    plt.plot(x, gaussian_filter1d(y, sigma=300))
    plt.plot(x, gaussian_filter1d(y, sigma=500))
    plt.plot(x, gaussian_filter1d(y, sigma=1000))
    # plt.vlines(range(0,int(x[-1]),60), -0.13, -0.225, colors='k', linestyles='solid', label='')
    plt.ylabel('amount of watts used on current time\'s update')
    plt.xlabel('time (s)')
    plt.show()

def draw_graphs(name, x, y1, y2):
    plt.title('Current Charge Plot ' + name)
    plt.subplot(2, 1, 1)
    # plt.vlines(range(0,int(x[-1]),60), -0.13, -0.17, colors='k', linestyles='solid', label='')
    plt.plot(x, gaussian_filter1d(y1, sigma=100))
    plt.plot(x, gaussian_filter1d(y1, sigma=300))
    plt.plot(x, gaussian_filter1d(y1, sigma=500))
    plt.plot(x, gaussian_filter1d(y1, sigma=1000))
    plt.ylabel('energy used at instance (joules)')
    plt.subplot(2, 1, 2)
    plt.plot(x, y2)

    # plt.vlines(range(0,int(x[-1]),60), 0, y2[-1], colors='k', linestyles='solid', label='')
    plt.xlabel('time (s)')
    plt.ylabel('total energy used (joules)')
    plt.show()

def main():
    # matplotlib.use('MacOSX')

    COLUMNS = [
        "global_time",
        "watts_used",
        "current_charge"
    ]

    mypath = "data/babyB/"
    onlyfiles = [f for f in listdir(mypath) if f.endswith('.txt')]

    n_iter = 120
    robot_average = None
    for file_name in onlyfiles:
        global_time = []
        watts_used = []
        current_charge = []

        draw30 = False # plot for first 30 seconds
        drawIter = True # plot for each iteration (60s)
        i = 1
        temp_w = []
        temp_c = []
        temp_diff = []



        with open(mypath + file_name, 'r') as file:
            for line in file:
                data = line.strip('\n').split(' ')
                global_time.append(float(data[0]))
                watts_used.append(float(data[1]))
                current_charge.append(float(data[2]))

                if drawIter:
                    temp_w.append(float(data[1]))
                    temp_c.append(float(data[2]))
                    if float(data[0]) > i * 60 :
                        temp_diff.append(temp_c[0]-temp_c[-1])
                        # draw_graphs(file_name +" iteration: "+ str(i),range(len(temp_c)), temp_w, temp_c)
                        # draw_graph(file_name +" iteration: "+ str(i),range(len(temp_c)), temp_w)
                        i += 1
                        temp_c.clear()
                        temp_w.clear()

                if float(data[0]) > 500 and draw30:
                    draw_graphs(file_name, global_time, watts_used, current_charge)
                    draw30 = False
            # draw_graph(file_name, global_time, watts_used)
            # draw_graphs(file_name, global_time, watts_used, current_charge)


            plt.plot(range(1, 121), temp_diff,marker='x')
            # plt.axis([0,120,6.4,14])
            plt.xlabel('iteration number')
            plt.ylabel('total energy used (joules)')
            plt.show()

            if robot_average is None:
                robot_average = np.array(temp_diff)
            else:
                robot_average += np.array(temp_diff)



    robot_average /= 10
    plt.title("the average of joules used per iteration of all robots")
    plt.plot(range(1, 121), robot_average ,marker='x')
    # plt.axis([0,120,6.4,14])
    plt.xlabel('iteration number')
    plt.ylabel('total energy used (joules)')
    plt.show()

if __name__ == "__main__":
    main()