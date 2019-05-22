#!usr/bin/env python3
"""
This script can be called to create plots of the fitness function. I use it after a run of BO.
It creates both a monotonic (increasing) fitness plot, as well as a fitness plot with all the
separate fitness points over time. It's written to the directory given.

Params:
arg1: The directory name that contains the fitness data fitnesses.txt
arg2: The number of initial samples drawn for BO
arg3: The number of iterations to test the best controller in the end
"""

import numpy as np
import sys
import matplotlib
from sys import platform

# Enable different backend for OSX
if platform == "darwin":
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

# Set matplotlib font
font = {'size' : 20}
matplotlib.rc('font', **font)

# Obtain arguments
try:
    root_directory = str(sys.argv[1])
    n_initial_samples = int(sys.argv[2])
    n_no_learning_iterations = int(sys.argv[3])
except IndexError:
    print("Please check the arguments of the directory/n_initial_samples/n_no_learning_iterations")

def fitness_per_iteration_plot(my_directory, my_data, n_initial_samples, n_no_learning_iterations):
    # Set up plot
    plt.figure(figsize=(14, 14))
    plt.xlabel("#Evaluations")
    plt.ylabel("Fitness")
    plt.title("CPG + BO")
    plt.axvline(x=n_initial_samples, color="green", linestyle="dashed")
    plt.axvline(x=len(my_data) - n_no_learning_iterations, color="red", linestyle="dashed")
    plt.grid()
    plt.plot(my_data[:-(n_no_learning_iterations + 1)])

    # Save plots
    plt.savefig(my_directory + "/fitness.png")


def max_fitness_plot(my_directory, my_data, n_initial_samples, n_no_learning_iterations):
    # Create monotonic sequence
    my_data = [e if e >= max(my_data[:ix+1]) else max(my_data[:ix+1]) for ix, e in enumerate(my_data)]

    # Set up plot
    plt.figure(figsize=(14, 14))
    plt.xlabel("#Evaluations")
    plt.ylabel("Fitness")
    plt.title("CPG + BO")
    plt.axvline(x=n_initial_samples, color="green", linestyle="dashed")
    plt.grid()
    plt.plot(my_data[:-(n_no_learning_iterations + 1)])

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

    # Get face
    face = [str(line.rstrip('\n')) for line in open(path + "face.txt")][0]

    # Exclude last comma while saving brain
    np.savetxt(path + "/best_brain.txt", [my_samples[ix_best][:-2] + "," + face], delimiter=",", fmt="%s")

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

print("root directory is ", root_directory)
save_best_brain(root_directory)
print("Plots are constructed  at ", root_directory)
