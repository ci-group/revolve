import matplotlib
import matplotlib.pyplot as plt
import numpy as np



from scipy.ndimage.filters import gaussian_filter1d


'''
MacOSX
TkAgg
TkCairo
'''

def average(n, lst):
    res = []
    for i in range(len(lst)//n):
        res.append(sum(lst[i*n:(i+1)*n])/n)
    return res


def draw_graph(x, y):
    plt.title('Battery Plot')
    # plt.plot(x, y)
    plt.plot(x, gaussian_filter1d(y, sigma=100))
    plt.plot(x, gaussian_filter1d(y, sigma=300))
    plt.plot(x, gaussian_filter1d(y, sigma=500))
    plt.plot(x, gaussian_filter1d(y, sigma=1000))

    plt.ylabel('energy used at instance (joules)')
    plt.xlabel('time (s)')
    plt.show()

def draw_graphs(x, y1, y2):
    plt.title('Battery Plot')
    plt.subplot(2, 1, 1)
    plt.plot(x, y1)
    plt.ylabel('energy used at instance (joules)')

    plt.subplot(2, 1, 2)
    plt.plot(x, y2)
    plt.xlabel('time (s)')
    plt.ylabel('total energy used (joules)')
    plt.show()

def main():
    # matplotlib.use('MacOSX')
    global_time = []
    watts_used = []
    current_charge = []
    draw30 = True
    with open('battery_info.txt', 'r') as file:
        for line in file:
            data = line.strip('\n').split(' ')
            global_time.append(float(data[0]))
            watts_used.append(float(data[1]))
            current_charge.append(float(data[2]))
            if float(data[0]) > 30 and draw30:
                # draw_graphs(global_time, watts_used, current_charge)
                draw30 = False
        draw_graph(global_time, watts_used)
        # draw_graphs(global_time, watts_used, current_charge)

if __name__ == "__main__":
    main()