import matplotlib
import matplotlib.pyplot as plt
import sys
import numpy as np

# Obtain arguments
root_directory = str(sys.argv[1])
n_initial_samples = int(sys.argv[2])
n_learning = int(sys.argv[3])


def plot_output(my_directory, my_data, x1, title):
    font = {'size': 20}
    matplotlib.rc('font', **font)

    # Set up plot
    plt.figure(figsize=(14, 14))
    plt.xlabel("#Evaluations")
    plt.ylabel("Fitness")
    plt.title("Spline + RLPower")
    plt.axvline(x=x1, color="green", linestyle="dashed")
    plt.grid()
    plt.plot(my_data)

    # Save plots
    plt.savefig(my_directory + "/" + title + ".pdf")
    plt.savefig(my_directory + "/" + title + ".png")


def get_data(my_directory, filename):
    # Read data
    filename = my_directory + filename
    my_data = [(line.rstrip('\n')) for line in open(filename)]
    my_data = np.matrix([x.split(",") for x in my_data], dtype=np.float)

    # Return data
    return my_data


# Main
fitness_data = get_data(root_directory, "fitness.txt")
plot_output(root_directory, fitness_data[:n_initial_samples + n_learning, 0], n_initial_samples, "gait")
plot_output(root_directory, fitness_data[:n_initial_samples + n_learning, 1], n_initial_samples, "left")
plot_output(root_directory, fitness_data[:n_initial_samples + n_learning, 2], n_initial_samples, "right")


print("Plots are constructed \n")
