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
path = "/home/maarten/CLionProjects/revolve/output/cpg_bo/main_1560423026-1-spider17/"
fitness_file = "fitnesses.txt"
yaml_temp_path = "/home/maarten/CLionProjects/revolve/experiments/bo_learner/yaml/yaml_temp/"
n_rows_min = 1450
n_rows_max = 1501  # This one defines the brain as well
max_dirs = 30

# Get all sub-directories
path_list = glob(path + "*")
path_list = [path_ for path_ in path_list if os.path.isdir(path_)]
n_dirs = len(path_list)

# Holder
results = np.empty((n_dirs, 3))
times = [100,250,500,1000,1501]

# Check if it's numeric:
fitness_list = []
subrun_numbers = []
open(path_list[0] + '/brain_all_1501.txt', 'w').close()

for i, path_ in enumerate(path_list):
    try:
        int(path_.split("/")[-1] )
    except:
        continue

    # Cope with unsorted issue
    path_ =  "/".join(path_.split("/")[:-1]) + "/" + str(i)

    # Clear files
    open(path_ + '/brain_all.txt', 'w').close()
    open(path_ + '/experiment_fitnesses.txt', 'w').close()

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

    # Check which paths don't have a brain.txt
    subfolder_list_temp_2 = []
    for j_, subfolder_ in enumerate(subfolder_list_temp):
        par = subfolder_list_temp
        if os.path.isfile(subfolder_ + "/brain.txt"):
            subfolder_list_temp_2 += [subfolder_]
        else:
            print("Exclude ", subfolder_, " due lack of brain")

    print(f"Select top {max_dirs} from {len(subfolder_list_temp_2)} directories")
    subfolder_list_temp_2 = subfolder_list_temp_2[:max_dirs]

    # Save the names of these brains in a txt file
    with open(path_ + "/brain_all.txt", 'a') as all_brain_file:
        for x in subfolder_list_temp_2:
            for time in times:
                all_brain_file.write('"'+ "'" + x + 'best_brain' + str(time) + ".txt" +  "'"  +'"'+ ",\n")

    with open(path_ + "/brain_all_1501.txt", 'a') as all_brain_file:
        for x in subfolder_list_temp_2:
            all_brain_file.write('"'+ "'" + x + 'best_brain1501.txt' +  "'"  +'"'+ ",\n")

    # Save this number of subruns
    n_subruns = len(subfolder_list_temp_2)
    subrun_numbers += [[n_subruns, i]]

    # Working variables
    fitnesses = np.empty((n_rows_max,n_subruns))
    fitnesses_mon = np.empty((n_rows_max,n_subruns))

    # Create plot
    plt.figure()
    plt.title(path.split("-")[-1][:-1].capitalize())
    plt.xlabel("Iteration")
    plt.ylabel("Fitness")
    plt.grid()

    # For all n_runs
    for j, subfolder in enumerate(subfolder_list_temp_2):
        # print( subfolder)
        # Get fitness file
        my_fitness = [float((line.rstrip('\n'))) for line in open(subfolder + "/" + fitness_file)]
        # Take maximum n_rows_max
        my_fitness = my_fitness[:n_rows_max]

        # Take minimum n_rows_max
        c_ = 0
        while len(my_fitness) < n_rows_max:
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
        with open(path_ + "/experiment_fitnesses.txt" , 'a') as experiment_fitness_file:
            experiment_fitness_file.write(",".join([str(my_fitness_mon[-1]), subfolder.split("/")[-2]]) + "\n")

        print(j,subfolder)

        # Save the brain to prevent dead references
        # Find index of best brain
        brain = [(line.rstrip('\n')) for line in open(subfolder + "/" + "brain.txt")]
        my_fitness_str = [str(x) for x in my_fitness]
        index_list =[]
        brain_list = []
        for b in brain:
            f = b.split(",")[-1]
            first_index = my_fitness_str.index(f)
            index_list += [first_index]

        # Find best brain under time constraint for a list of times
        for time in times:
            for ix, e in enumerate(index_list):
                if e > time:
                    ix -= 1
                    break

            try:
                nb1 = index_list[ix-1]
                nb2 = index_list[ix+1]
                print(f"Brain with time {index_list[ix]} neighbours are {index_list[ix-1]} and {index_list[ix+1]}")
            except:
                print(f"Brain with time {index_list[ix]} has at most 1 neighbour")

            # Write this brain
            open(subfolder + "/" + "/best_brain" + str(time) +".txt", 'w').close()
            with open(subfolder + "/" + "/best_brain" + str(time) +".txt", 'a') as brain_file:
                brain_file.write(brain[ix] +"\n")

        # Plot the avg fitness
        plt.plot(fitnesses_mon[:, j], linewidth = 0.5, color = "blue")

    # Take average value over the n_runs
    avg_fitness = np.mean(fitnesses, axis=1)
    avg_fitness_mon = np.mean(fitnesses_mon, axis=1)

    # Save plot
    plt.plot(avg_fitness_mon, linestyle="dashed", linewidth=2.5, color="black")
    plt.xlim(0,1500)
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
open(path + '/results.txt', 'w').close()
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
