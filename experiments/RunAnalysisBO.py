import matplotlib
matplotlib.use("TkAgg") # For Mac OS X
import matplotlib.pyplot as plt
import sys

# Obtain arguments
root_directory = str(sys.argv[1])
n_initial_samples = int(sys.argv[2])
n_no_learning_iterations = int(sys.argv[3])


def plot_output(my_directory, my_data, x1, x2):
    font = {'size'   : 20}
    matplotlib.rc('font', **font)

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
    plt.savefig(my_directory + "/fitness.pdf")
    plt.savefig(my_directory + "/fitness.png")


def get_data(my_directory, filename):
    # Read data
    filename = my_directory + filename
    my_data = [float(line.rstrip('\n')) for line in open(filename)]

    # Return data
    return my_data


# Main
fitness_data = get_data(root_directory, "fitnesses.txt")
plot_output(root_directory, fitness_data, n_initial_samples, n_no_learning_iterations)

print("Plots are constructed \n")
