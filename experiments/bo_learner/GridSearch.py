import numpy as np
import itertools
import os
import time
import matplotlib.pyplot as plt
from glob import glob

# Parameters
n_runs = 5
search_space = {
    'self.signal_factor': [1.5, 2.0, 2.5],
    'self.init_neuron_state': [0.5, 0.7],
}
# Name of the file
my_filename = "pyrevolve/revolve_bot/brain/bo_cpg.py"
output_path = "output/cpg_bo/"


def change_parameters(original_file, parameters):
    # Iterate over dictionary elements
    for key, value in iter(parameters.items()):
        # Find first occurrence of parameter
        ix = [row for row in range(len(original_file)) if key in original_file[row]][0]

        # Change values. Note the Python indentation
        original_file[ix] = "        " + key + " = " + str(value)

    # Return adapted file:
    return original_file


def write_file(filename, contents):
    # Write back to file
    with open(filename, 'w') as file:
        # Write updated contents
        for line in contents:
            file.write(line + "\n")
        file.close()


if __name__ == "__main__":
    # Read file
    py_file = [(line.rstrip('\n')) for line in open(my_filename)]

    # Get permutations
    keys, values = zip(*search_space.items())
    experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

    # Save directory names
    all_directories = []
    main_dir = "main-" + str(round(time.time()))

    # Create dirs
    os.mkdir(output_path + main_dir)
    os.mkdir(output_path + main_dir + "/plots")

    # Run experiments
    avg_fitness_dict = {}
    for experiment_params in experiments:
        print(experiment_params)

        # List of directories for this experiment.
        experiment_directories = []

        # Repeat n_runs times
        for i in range(n_runs):
            # Change the file
            py_file = change_parameters(py_file, experiment_params)

            # Write to file
            write_file(my_filename, py_file)

            # Call the experiment
            py_command = "~/projects/revolve-simulator/revolve/.venv36/bin/python3.6" \
                         " ./revolve.py " \
                         "--manager experiments/bo_learner/manager.py"
            os.system(py_command)

            # Save the newest directory
            directories = glob(output_path + "*/")
            directories = [x[:-1] for x in directories]
            directories = [int(dir.split("/")[-1].split("-")[-1]) for dir in directories]
            newest_directory = max(directories)
            experiment_directories += [newest_directory]

        # Save list of directories
        all_directories += [experiment_directories]

    # Create a fitness dictionary with key = directory, val = avg_fitness
    avg_fitness_dict = {}

    # Allow some time for Clion re-indexing
    time.sleep(5)

    # Run experiments
    for experiments in all_directories:
        # Create empty matrix
        n_rows = len([(line.rstrip('\n')) for line in open(output_path + str(experiments[-1]) + "/fitnesses.txt")])
        fitnesses = np.empty((n_rows, n_runs))
        fitnesses_mon = np.empty((n_rows, n_runs))

        # Plot details
        plt.figure()
        plt.title("Monotonic - all runs")
        plt.xlabel("Iteration")
        plt.ylabel("Fitness")
        plt.grid()

        # Load all the fitness values,and average them
        for ix, experiment in enumerate(experiments):
            # Load fitness
            fitness = [float((line.rstrip('\n'))) for line in open(output_path + str(experiment) + "/fitnesses.txt")]

            # Transfer fitness to monotonic sequence and save
            fitness_mon = [e if e >= max(fitness[:ix+1]) else max(fitness[:ix+1]) for ix, e in enumerate(fitness)]

            # Save fitness
            fitnesses_mon[:, ix] = np.array(fitness_mon)
            fitnesses[:, ix] = np.array(fitness)

            # Plot the avg fitness
            plt.plot(fitnesses_mon[:, ix], linewidth = 1.5)

        # Take average value over the n_runs
        avg_fitness = np.mean(fitnesses, axis=1)
        avg_fitness_mon = np.mean(fitnesses_mon, axis=1)

        # Save plot
        plt.plot(avg_fitness_mon, linestyle="dashed", linewidth=2.5, color="black")
        plt.savefig(output_path + main_dir + "/plots/" + str(round(avg_fitness_mon[-1], 5)) + ".png")

        # Save avg fitness
        experiments = [str(e) for e in experiments]
        avg_fitness_dict[','.join(experiments)] = avg_fitness_mon[-1]

    # Write results of the run to output_path + main
    avg_fitness_dict = dict(sorted([(value, key) for (key, value) in avg_fitness_dict.items()], reverse=True))

    # Store sorted fitness
    print("Fitness - directories")
    for key, value in avg_fitness_dict.items():
        # Write to console
        print("{} - {}".format(key, value))

        # Write to file in main directory
        with open(output_path + main_dir + '/fitnesses.txt', 'a') as avg_fitness_file:
            avg_fitness_file.write(str(key) + "-" + str(value) + "\n")

    print("Contents written to ", output_path + main_dir)
