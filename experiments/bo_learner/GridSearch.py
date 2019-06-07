"""
    experiments = [
        {'range_ub': 1.0, 'signal_factor_all': 1.0},
        {'range_ub': 1.0, 'signal_factor_all': 3.0},
        {'range_ub': 4.5, 'signal_factor_all': 3.0}
    ]
"""
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
min_lines = 1450
run_gazebo = False
n_runs = 20 # Naar 20
run_factor = 5
n_jobs = 60
my_yaml_path = "experiments/bo_learner/yaml/"
yaml_model = "babyA.yaml"
manager = "experiments/bo_learner/manager.py"
python_interpreter = ".venv/bin/python3"
search_space = {
    'n_learning_iterations': [1500],
    'n_init_samples': [20],
    'evaluation_rate': [60],
    'verbose': [0],
    'kernel_sigma_sq': [1],
    'kernel_l': [0.02, 0.05, 0.1, 0.2],
    'acqui_ucb_alpha': [0.1, 0.3, 0.5, 1.0],
    'range_ub': [1.5],
    'signal_factor_all': [4.0],
}

print(search_space)
# You don't have to change this
my_sub_directory = "yaml_temp/"
output_path = "output/cpg_bo/main_" + str(round(time.time())) + "/"
start_port = 11345
finished = False

# Make in revolve/build to allow runs from terminal
#os.system('nmcli connection up id "Ripper intranet"')
os.system('cmake /home/gongjinlan/projects/revolve/ -DCMAKE_BUILD_TYPE="Release"')
os.system("make -j60")
#os.system('nmcli connection down id "Ripper intranet"')

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
        time.sleep(5*i)
    else:
        print("Todo: Make sure you are leaving 2 seconds in between firing "
              "gazebos")

    # Get yaml file id
    k = params["id"]

    my_time = str(round(time.time(), 2))
    my_run_path = output_path + str(k) + "/" + my_time + "/"
    os.mkdir(my_run_path)

    # Select relevant yaml file
    yaml_model = my_yaml_path + sub_directory + model.split(".yaml")[0] + "-" + str(k) + ".yaml"
    print(yaml_model)
    # Get relevant yaml file
    yaml_file = [(line.rstrip('\n')) for line in open(yaml_model)]

    # Change output_directory
    index = [ix for ix, x in enumerate(yaml_file) if "output_directory" in x][0]
    yaml_file[index] = f'    output_directory: "{my_run_path}"'

    # Write temporarily with identifier
    write_file(my_yaml_path + sub_directory + model.split(".yaml")[0] + "-" + str(k) + "-" + str(i) + ".yaml", yaml_file)
    yaml_model = my_yaml_path + sub_directory + model.split(".yaml")[0] + "-" + str(k) + "-" + str(i) + ".yaml"

    # Change port: We need to do this via the manager
    world_address = "127.0.0.1:" + str(start_port + i)
    os.environ["GAZEBO_MASTER_URI"] = "http://localhost:" + str(start_port + i)
    os.environ["LIBGL_ALWAYS_INDIRECT"] = "0"
    py_command = ""

    # Call the experiment
    if not run_gazebo:
        py_command = python_interpreter + \
                     " ./revolve.py" + \
                     " --manager " + manager + \
                     " --world-address " + world_address + \
                     " --robot-yaml " + yaml_model
    else:
        py_command = python_interpreter + \
                     " ./revolve.py" + \
                     " --manager " + manager + \
                     " --world-address " + world_address + \
                     " --robot-yaml " + yaml_model + \
                     " --simulator-cmd gazebo" \

    return_code = os.system(py_command)
    if return_code == 32512:
        print("Specify a valid python interpreter in the parameters")


if __name__ == "__main__":
    # Get permutations
    keys, values = zip(*search_space.items())
    experiments = [dict(zip(keys, v)) for v in itertools.product(*values)]

    # PASTE THE EXPERIMENTS HERE, IN THE FORMAT SHOWN BELOW
    experiments = [
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 0.5},   # BASE RUN

        # BASE RUN
        {'init_method': "LHS", 'kernel_l': 0.2, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 0.5},
        {'init_method': "LHS", 'kernel_l': 0.5, 'kernel_sigma_sq': 1.0, 'acqui_ucb_alpha': 0.5},
        {'init_method': "LHS", 'kernel_l': 1.0, 'kernel_sigma_sq': 1.0, 'acqui_ucb_alpha': 0.5},
        {'init_method': "LHS", 'kernel_l': 1.5, 'kernel_sigma_sq': 1.0, 'acqui_ucb_alpha': 0.5},

        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 0.1,  'acqui_ucb_alpha': 0.5},
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 0.2,  'acqui_ucb_alpha': 0.5},
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 0.5,  'acqui_ucb_alpha': 0.5},
        # BASE RUN

        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 0.1},
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 0.2},
        # BASE RUN
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 1.0},
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 1.5},
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 2.0},
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 3.0},
        {'init_method': "LHS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 4.0},

        {'init_method': "RS", 'kernel_l': 0.1, 'kernel_sigma_sq': 1.0,  'acqui_ucb_alpha': 0.5},
        # BASE RUN
    ]
    # 'kernel_l': [0.02, 0.05, 0.1, 0.2],
    # 'acqui_ucb_alpha': [0.1, 0.3, 0.5, 1.0],
    unique_experiments = experiments
    n_unique_experiments = len(experiments)

    # Get id's on the permutations
    for ix, my_dict in enumerate(experiments):
        my_dict["id"] = ix

    # Create a list with parameters to iterate over
    experiments *= n_runs*run_factor

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

    # Create experiment group directories
    for i in range(n_unique_experiments):
        os.mkdir(output_path + str(i) + "/")

    while not finished:
        with Parallel(n_jobs=n_jobs) as parallel:
            # Run experiments in parallel
            try:
                parallel(delayed(run)(i,
                                     my_sub_directory,
                                     yaml_model,
                                     experiment) for i, experiment in enumerate(experiments))
            except:
                print("Some runs are killed by timeout")

            # Count number of finished runs for all experiments. Read this from the parameters file
            runs_succesful = {}
            experiment_list = glob(output_path + "*/")

            for ix,e in enumerate(experiment_list):
                runs = glob(e + "*/")
                runs_succesful[str(e.split("/")[-2])] = 0

                for my_run in runs:
                    if os.path.isfile(my_run + "fitnesses.txt"):
                        n_lines = len([(line.rstrip('\n')) for line in open(my_run + "fitnesses.txt")])

                        # In case we had a succesful run
                        if n_lines > min_lines:
                            runs_succesful[str(e.split("/")[-2])] += 1

            to_run = {}
            for key, val in runs_succesful.items():
                to_run[key] = n_runs - val
            to_run = {k: v for k, v in to_run.items() if v > 0}

            # If the experiment list is empty
            if not bool(to_run):
                finished = True
            else:
                print(f"To finish {sum(to_run.values())} runs")

                # Empty experiments list
                experiments = []

                # Use spare computing capacity
                while sum(to_run.values()) < n_jobs - len(to_run):
                    print(to_run)

                    for key, value in to_run.items():
                        to_run[key] += 1

                # Construct new experiment list
                for key, val in to_run.items():
                    for i in range(val):
                        entry = unique_experiments[int(key)]
                        experiments.append(entry)

    # START ANALYSIS HERE
    print("I will now perform analysis")

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
