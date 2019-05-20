from sys import platform
import matplotlib
if platform == "darwin":
    matplotlib.use("TkAgg")
import numpy as np
import itertools
import os
import time
import matplotlib.pyplot as plt
from glob import glob
from joblib import Parallel, delayed

# Parameters
n_runs = 2
n_jobs = 1
my_yaml_path = "experiments/bo_learner/yaml/"
yaml_model = "spider9.yaml"
manager = "experiments/bo_learner/manager.py"
python_interpreter = ".venv/bin/python3"
search_space = {
    'n_learning_iterations': [5],
    'n_init_samples': [12],
    'evaluation_rate': [100],
    'use_frame_of_reference:': [0],
    'verbose': [1],
    'signal_factor_all': [4.0],
}

print(search_space)
# You don't have to change this
my_sub_directory = "yaml_temp/"
output_path = "output/cpg_bo/main_" + str(round(time.time())) + "/"
start_port = 11345


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
            file.write((line + "\n"))
        file.close()


def create_yamls(yaml_path, model, sub_directory, experiments):
    # Read original yaml file
    yaml_file = [(line.rstrip('\n')) for line in open(yaml_path + model)]

    # Change yaml file
    for my_dict in experiments:
        # Loop over the entries in this dict
        for key, value in my_dict.items():
            if not key == "id":
                # Check on what line this parameter is
                index = [ix for ix, x in enumerate(yaml_file) if key in x][0]

                yaml_file[index] = "    " + key + ": " + str(value)

        # Write yaml file to desired location
        write_file(yaml_path + sub_directory + "/" + yaml_model.split(".")[0] + "-" + str(my_dict["id"]) + ".yaml", yaml_file)


def run(i, sub_directory, model, params):
    # Sleepy time when starting up to save gazebo from misery
    if i < n_jobs:
        time.sleep(i)
    else:
        print("Todo: Make sure you are leaving 2 seconds in between firing "
              "gazebos")

    # Get yaml file id
    k = params["id"]

    # Select relevant yaml file
    yaml_model = my_yaml_path + sub_directory + model.split(".yaml")[0] + "-" + str(k) + ".yaml"

    # Get relevant yaml file
    yaml_file = [(line.rstrip('\n')) for line in open(yaml_model)]

    # Change output_directory
    index = [ix for ix, x in enumerate(yaml_file) if "output_directory" in x][0]
    yaml_file[index] = "    output_directory: " + output_path + str(k) + "/" + str(i) + "/"

    # Write temporarily with identifier
    write_file(my_yaml_path + sub_directory + model.split(".yaml")[0] + "-" + str(k) + "-" + str(i) + ".yaml", yaml_file)
    yaml_model = my_yaml_path + sub_directory + model.split(".yaml")[0] + "-" + str(k) + "-" + str(i) + ".yaml"

    # Change port: We need to do this via the manager
    world_address = "127.0.0.1:" + str(start_port + i)
    os.environ["GAZEBO_MASTER_URI"] = "http://localhost:" + str(start_port + i)
    os.environ["LIBGL_ALWAYS_INDIRECT"] = "0"

    # Call the experiment
    py_command = python_interpreter + \
                 " ./revolve.py" \
                 " --manager " + manager + \
                 " --world-address " + world_address + \
                 " --robot-yaml " + yaml_model + \
                 " --simulator-cmd gazebo"

    return_code = os.system(py_command)
    if return_code == 32512:
        print("Specify a valid python interpreter in the parameters")


if __name__ == "__main__":
    # Get permutations
    keys, values = zip(*search_space.items())
    experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]
    n_unique_experiments = len(experiments)

    # Get id's on the permutations
    for ix, my_dict in enumerate(experiments):
        my_dict["id"] = ix

    # Create a list with parameters to iterate over
    experiments *= n_runs

    # Save to yaml files
    create_yamls(yaml_path=my_yaml_path,
                 model=yaml_model,
                 sub_directory=my_sub_directory,
                 experiments=experiments
                 )

    # Create dirs
    if not os.path.isdir("output"):
        os.mkdir("output")
    if not os.path.isdir("output/cpg_bo"):
        os.mkdir("output/cpg_bo")
    os.mkdir(output_path)
    for l in range(n_unique_experiments):   # Create dirs

        os.mkdir(output_path + str(l) + "/")

    # Run experiments in parallel
    Parallel(n_jobs=n_jobs)(delayed(run)(i,
                                         my_sub_directory,
                                         yaml_model,
                                         experiment) for i, experiment in enumerate(experiments))

    # Do analysis
    fitness_list = []
    for i in range(n_unique_experiments):
        path = output_path + str(i) + "/*/"
        path_list = glob(path)
        path_list = [my_path for my_path in path_list if os.path.exists(my_path + "fitnesses.txt")]
        n_rows = len([(line.rstrip('\n')) for line in open(path_list[0] + "fitnesses.txt")])
        n_subruns = len(path_list)

        # Working variables
        fitnesses = np.empty((n_rows,n_subruns))
        fitnesses_mon = np.empty((n_rows,n_subruns))

        # Create plot
        plt.figure()
        plt.title("Monotonic - Param setting " + str(i))
        plt.xlabel("Iteration")
        plt.ylabel("Fitness")
        plt.grid()

        # Get sub-runs for this setup
        for ix, e in enumerate(path_list):
            # Read fitness
            my_fitness = [float((line.rstrip('\n'))) for line in open(e + "fitnesses.txt")]

            # Transfer fitness to monotonic sequence and save
            my_fitness_mon = [e if e >= max(my_fitness[:ix+1]) else max(my_fitness[:ix+1]) for ix, e in enumerate(my_fitness)]

            # Save fitness
            fitnesses_mon[:,ix] = np.array(my_fitness_mon)
            fitnesses[:,ix] = np.array(my_fitness)

            # Plot the avg fitness
            plt.plot(fitnesses_mon[:, ix], linewidth = 1, color = "blue")

        # Take average value over the n_runs
        avg_fitness = np.mean(fitnesses, axis=1)
        avg_fitness_mon = np.mean(fitnesses_mon, axis=1)

        # Save plot
        plt.plot(avg_fitness_mon, linestyle="dashed", linewidth=2.5, color="black")
        plt.tight_layout()
        plt.savefig(output_path + str(i) + "/" + str(round(avg_fitness_mon[-1], 7)) + ".png")

        # Save fitness
        fitness_list += [[round(avg_fitness_mon[-1], 5), i]]

    # Get fitness stats
    fitness_list.sort(key=lambda x: x[0])
    fitness_list.reverse()
    fitness_list

    print("Fitnesses are:")
    for e in fitness_list:
        print(e)
        e = [str(e_) for e_ in e]
        # Write to file in main directory
        with open(output_path + '/results.txt', 'a') as avg_fitness_file:
            avg_fitness_file.write(",".join(e) + "\n")

    print("Contents written to ", output_path)

    # Delete the yaml's
    yaml_temp = my_yaml_path + my_sub_directory
    yaml_files = glob(yaml_temp + "*")
    for f in yaml_files:
        os.remove(f)

    # Write the parameters
    params_string =[]
    for key, value in iter(search_space.items()):
        params_string += [str(key) + ": " + str(value)]
    write_file(output_path + "search_space.txt", params_string)
