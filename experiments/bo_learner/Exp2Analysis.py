from glob import glob
import os
import numpy as np

path = "/home/maarten/CLionProjects/revolve/output/cpg_bo/main_1560453281-2-gecko7/"
path_list = glob(path + "/*/")
path_list = [path_ for path_ in path_list if os.path.isdir(path_)]
n_objects = 10


# Group based on value of p. Make mapping between number and p. This goes wrong.
p_dict  = {}
for ix, path_ in enumerate(path_list):
    subpaths = glob(path_ + "/*/")
    for subpath in subpaths:
        if os.path.isfile(subpath + "/" + "parameters.txt"):
            parameters = [(line.rstrip('\n')) for line in open(subpath + "/" + "parameters.txt")]
            for e in parameters:
                if "For slower amplitude factor" in e:
                    print(e)
                    break

            p = float(e.split(' ')[-1])
            print(p)
            p_dict[str(ix)] = round(p,2)

run_counter = {}
p_fitness = {}
for p in set(p_dict.values()):
    p_fitness[str(p)] = []

# Walk through the paths.
for ix, path_ in enumerate(path_list):
    number = path_.split("/")[-2]
    run_counter[number] = 0
    subfolders = glob(path_ + "/*/")
    means = []

    # D checks
    c = 0
    subfolders_1 = []
    for subfolder in subfolders:
        if os.path.isfile(subfolder + "/speed_to_object.txt"):
            speeds = [(line.rstrip('\n')) for line in open(subfolder + "/speed_to_object.txt")]
            if len(speeds) >= 10:
                subfolders_1 += [subfolder]
    if(len(subfolders_1) ==0):
        print("Failed run ", number)

    for subfolder in subfolders_1:
        # Get average speed to object for this path (if it exists, else continue)
        speeds = [(line.rstrip('\n')) for line in open(subfolder + "/speed_to_object.txt")][1:]

        speeds_filtered = []
        for e in speeds:
            speed = float(e.split(",")[-3])
            speeds_filtered += [speed]

        # Save
        my_mean = round(sum(speeds_filtered)/len(speeds_filtered),5)

        # Save run counter
        run_counter[number] = 1

        # Get p. This goes fine
        my_key = subfolder.split("/")[-3]
        #print(f"{subfolder} has key {my_key}")
        try:
            p = p_dict[my_key]

            # Save fitness
            p_fitness[str(p)] += [my_mean]
            break
        except:
            None

#  Analysis
missing_runs = {}
for key, value in run_counter.items():
    try:
        missing_runs[p_dict[str(key)]] = 0
    except:
        None

for key, value in run_counter.items():
    if value == 0:
        try:
            missing_runs[p_dict[str(key)]] +=1
        except:
            print("Missing pram file for", str(key))

open(path + "/speed_results.txt", "w").close()
print("\nMissing")
with open(path + '/speed_results.txt', 'a') as my_file:
    my_file.write("Missing:\n")

for key, value in missing_runs.items():
    print(key, value)
    with open(path + '/speed_results.txt', 'a') as my_file:
        my_file.write(str(key) + "," + str(value)+ "\n")

with open(path + '/speed_results.txt', 'a') as my_file:
    my_file.write("\nSpeeds:\n")

print("\nFitnesses")
for key, value in p_fitness.items():
    my_mean = round(np.mean(value),4)
    my_error = 1.96*np.std(value)/np.sqrt(len(value))
    print(len(value), key, my_mean, my_error)
    with open(path + '/speed_results.txt', 'a') as my_file:
        my_file.write(str(key) + "," + str(my_mean)+ "," + str(my_error)+ "\n")