import matplotlib
from sys import platform
# Enable different backend for OSX
if platform =="darwin":
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import numpy as np
import sys

# Set matplotlib font
font = {'size'   : 20}
matplotlib.rc('font', **font)

# Obtain arguments
root_directory = str(sys.argv[1])
n_initial_samples = int(sys.argv[2])
n_no_learning_iterations = int(sys.argv[3])


def fitness_per_iteration_plot(my_directory, my_data, x1, x2):
    # Set up plot
    plt.figure(figsize=(14, 14))
    plt.xlabel("#Evaluations")
    plt.ylabel("Fitness")
    plt.title("CPG + BO")
    plt.axvline(x=x1, color="green", linestyle="dashed")
    plt.axvline(x=len(my_data) - x2, color="red", linestyle="dashed")
    plt.grid()
    plt.plot(my_data)

    # Save plots
    plt.savefig(my_directory + "/fitness.png")


def max_fitness_plot(my_directory, my_data, x1, x2):
    # Create monotonic sequence
    my_data = [e if e >= max(my_data[:ix+1]) else max(my_data[:ix+1]) for ix, e in enumerate(my_data)]

    # Set up plot
    plt.figure(figsize=(14, 14))
    plt.xlabel("#Evaluations")
    plt.ylabel("Fitness")
    plt.title("CPG + BO")
    plt.axvline(x=x1, color="green", linestyle="dashed")
    plt.axvline(x=len(my_data) - x2, color="red", linestyle="dashed")
    plt.grid()
    plt.plot(my_data)

    # Save plots
    plt.savefig(my_directory + "/fitness_monotonic.png")


def get_data(my_directory, filename):
    # Read data
    filename = my_directory + filename
    my_data = [float(line.rstrip('\n')) for line in open(filename)]

    # Return data
    return my_data


def save_best_brain(path):
    my_fitness = [float(line.rstrip('\n')) for line in open(path + "fitnesses.txt")]
    my_samples = [line.rstrip('\n') for line in open(path + "samples.txt")]
    ix_best = np.argmax(my_fitness)
    # Exclude last comma while saving brain
    np.savetxt(path + "/best_brain.txt", [my_samples[ix_best][:-2]], delimiter=",", fmt="%s")


# Get and process data
fitness_data = get_data(root_directory, "fitnesses.txt")

fitness_per_iteration_plot(root_directory,
                           fitness_data,
                           n_initial_samples,
                           n_no_learning_iterations)

max_fitness_plot(root_directory,
                 fitness_data,
                 n_initial_samples,
                 n_no_learning_iterations)

save_best_brain(root_directory)

print("Plots are constructed \n")
