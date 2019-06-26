from sys import platform
import matplotlib
import numpy as np
import os
from glob import glob
if platform == "darwin":
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import time

# Parameters
path = "/home/gongjinlan/projects/revolve/output/cpg_bo/main_1559644358-BO-gecko7/"
fitness_file = "fitnesses.txt"
yaml_temp_path = "/home/gongjinlan/projects/revolve/experiments/bo_learner/yaml/yaml_temp/"

# Get all sub-directories
path_list = glob(path + "*")
path_list = [path_ for path_ in path_list if os.path.isdir(path_)]
n_dirs = len(path_list)
max_dirs = 20
n_rows_max = 1500
n_rows_min = 1450

# Holder
results = np.empty((n_dirs, 3))

# Check if it's numeric:
fitness_list = []
subrun_numbers = []
for i, path_ in enumerate(path_list):
    try:
        int(path_.split("/")[-1] )
    except:
        continue

    # Cope with unsorted issue
    path_ =  "/".join(path_.split("/")[:-1]) + "/" + str(i)

    # Do fitness analysis
    subfolder_list = glob(path_ + "/*/")
    subfolder_list = [d for d in subfolder_list if os.path.isfile(d + fitness_file)]
    try:
        n_rows = len([(line.rstrip('\n')) for line in open(subfolder_list[0] + "/" + fitness_file)])
    except:
        None

    # Remove all rows with a small number of values
    subfolder_list_temp = []
    for j_, subfolder_ in enumerate(subfolder_list):
        # Get fitness file
        my_fitness_ = [(line.rstrip('\n')) for line in open(subfolder_ + "/" + fitness_file)]
        if len(my_fitness_) >= n_rows_min:
            subfolder_list_temp += [subfolder_]
        else:
            print("Exclude ", subfolder_, "length", len(my_fitness_))

    # Save thisnumber of subruns
    n_subruns = len(subfolder_list_temp)
    subrun_numbers += [[n_subruns, i]]

    # Working variables
    fitnesses = np.empty((n_rows_max,n_subruns))
    fitnesses_mon = np.empty((n_rows_max,n_subruns))

    # Create plot
    plt.figure()
    plt.title("Monotonic - Param setting " + str(i))
    plt.xlabel("Iteration")
    plt.ylabel("Fitness")
    plt.grid()

    # Clean file
    open(path_ + "/experiment_fitnesses.txt", 'w').close()
    kx = 0

    # For all n_runs
    for j, subfolder in enumerate(subfolder_list_temp):
        # print( subfolder)
        # Get fitness file
        my_fitness = [float((line.rstrip('\n'))) for line in open(subfolder + "/" + fitness_file)]
        # Take maximum n_rows_max
        my_fitness = my_fitness[:n_rows_max]

        # Take minimum n_rows_max
        c_ = 0
        while(len(my_fitness) < n_rows_max):
            my_fitness += [my_fitness[-1]]
            c_ += 1

        if c_ >0:
            print(f"Added {c_} fitnesses for {subfolder}")

        # Transfer fitness to monotonic sequence and save
        my_fitness_mon = [e if e >= max(my_fitness[:ix+1]) else max(my_fitness[:ix+1]) for ix, e in enumerate(my_fitness)]

        # Save fitness
        fitnesses_mon[:,j] = np.array(my_fitness_mon)
        fitnesses[:,j] = np.array(my_fitness)

        # Save the fitnesses of all runs
        with open(path_ + "/experiment_fitnesses.txt", 'a') as experiment_fitness_file:
            if kx < max_dirs:
                experiment_fitness_file.write(",".join([str(my_fitness_mon[-1]), subfolder.split("/")[-2]]) + "\n")
                kx += 1

        # Plot the avg fitness
        plt.plot(fitnesses_mon[:, j], linewidth = 1, color = "blue")

    # Take average value over the n_runs
    avg_fitness = np.mean(fitnesses, axis=1)
    avg_fitness_mon = np.mean(fitnesses_mon, axis=1)

    # Save plot
    plt.plot(avg_fitness_mon, linestyle="dashed", linewidth=2.5, color="black")
    plt.tight_layout()
    plt.savefig(path_ + "/" + str(round(avg_fitness_mon[-1], 7)) + ".png")
    fig = plt.gcf()
    plt.close(fig)

    # Save fitness
    fitness_list += [[round(avg_fitness_mon[-1], 5), i]]

# Get fitness stats
fitness_list.sort(key=lambda x: x[0])
fitness_list.reverse()
fitness_list


# TODO: Results.txt has wrong order (3D plot not affected by this).
print("Fitnesses are:")
for e in fitness_list:
    print(e)
    e = [str(e_) for e_ in e]
    # Write to file in main directory
    with open(path + '/results.txt', 'a') as avg_fitness_file:
        avg_fitness_file.write(",".join(e) + "\n")

print("Number of succesful runs:")
for l in range(len(subrun_numbers)):
    print(subrun_numbers[l])

print("Contents written to ", path)

# Delete the yaml's
yaml_files = glob(yaml_temp_path + "*")
for f in yaml_files:
    os.remove(f)

