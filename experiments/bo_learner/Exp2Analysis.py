from glob import glob
import os
import numpy as np

path = "/home/maarten/CLionProjects/revolve/output/cpg_bo/main_1560464548-2-gecko17/"
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
                    break

            p = float(e.split(' ')[-1])
            p_dict[str(ix)] = round(p,2)

run_counter = {}
p_fitness = {}
fail_counter = {}
slow_counter = {}
for p in set(p_dict.values()):
    p_fitness[str(p)] = []
    fail_counter[str(p)] = []
    slow_counter[str(p)] = []

# Walk through the paths.
for ix, path_ in enumerate(path_list):
    object_reached = True
    number = path_.split("/")[-2]
    run_counter[number] = 0
    subfolders = glob(path_ + "/*/")
    means = []
    c = 0


    """
    Todo:
    1: Only consider folders that have a speed to object file and a dist_to_object file. These are successes
    2: Take 1 run for each. 
    For this folder:
        If len(speed_to_object) < 10 and len(dist_to_object) >= 400, the run is too slow. 
            Save it in slow_counter[p] +=[number]
        Else the run has succeeded
    """

    # 1. Only consider folders that have a speed to object file and a dist_to_object file. These are successes
    subfolders_1 = []
    for subfolder in subfolders:
        if os.path.isfile(subfolder + "/speed_to_object.txt"):
            if os.path.isfile(subfolder + "/dist_to_object.txt"):
                subfolders_1 += [subfolder]

    # Take 1 run:
    if len(subfolders_1) == 0:
        fail_counter[str(p_dict[str(number)])] += [number]
        print("Failed - 1")
        continue
    else:
        subfolder = subfolders_1[0]

    # get speeds and distances
    speeds = [(line.rstrip('\n')) for line in open(subfolder + "/speed_to_object.txt")][1:]
    dists  = [(line.rstrip('\n')) for line in open(subfolder + "/dist_to_object.txt")]
    print(speeds, len(speeds), len(dists))
    # Check if we are fast enough
    if len(speeds) < 10 and len(dists) >= 399:
        slow_counter[str(p_dict[str(number)])] += [number]
        print("Too slow")
        continue

    # Check if we are fast enough
    if len(speeds) < 10 and len(dists) < 400:
        fail_counter[str(p_dict[str(number)])] += [number]
        print("Failed - 2")
        continue

    # Get average speed
    speeds_filtered = []
    for e in speeds:
        speed = float(e.split(",")[-3])
        speeds_filtered += [speed]

    # Save average speed
    my_mean = round(sum(speeds_filtered)/len(speeds_filtered),5)

    # Get p. This goes fine
    my_key = subfolder.split("/")[-3]
    p = p_dict[my_key]

    # Save fitness
    p_fitness[str(p)] += [my_mean]

# if len(speeds) >= 10:
#                 subfolders_1 += [subfolder]
#     if(len(subfolders_1) ==0):
#         print("Failed run ", number)
#
#     # All subfolderse in here have a speed to object of length 10
#     # Check if runs are too slow
#     subfolders_2 = []
#     for subfolder in subfolders_1:
#         if os.path.isfile(subfolder + "/dist_to_object.txt"):
#             dists = [(line.rstrip('\n')) for line in open(subfolder + "/dist_to_object.txt")]
#             if len(dists) >= 400:
#                 subfolders_2 += [subfolder]
#
#
#
#     if(len(subfolders_2) ==0):
#         slow_counter[str(p_dict[str(number)])] += [number]
#         print("Too slow run ", path_)
#     else:
#         for subfolder in subfolders_2:
#             # Get average speed to object for this path (if it exists, else continue)
#             speeds = [(line.rstrip('\n')) for line in open(subfolder + "/speed_to_object.txt")][1:]
#
#             speeds_filtered = []
#             for e in speeds:
#                 speed = float(e.split(",")[-3])
#                 speeds_filtered += [speed]
#
#             # Save
#             my_mean = round(sum(speeds_filtered)/len(speeds_filtered),5)
#
#             # Save run counter
#             run_counter[number] = 1
#
#             # Get p. This goes fine
#             my_key = subfolder.split("/")[-3]
#             #print(f"{subfolder} has key {my_key}")
#             try:
#                 p = p_dict[my_key]
#
#                 # Save fitness
#                 p_fitness[str(p)] += [my_mean]
#                 break
#             except:
#                 None

#  Analysis
# failed_runs = {}
# print(fail_counter)
# for key, value in fail_counter.items():
#     try:
#         failed_runs[p_dict[str(key)]] = 0
#     except:
#         None
#
# for key, value in fail_counter.items():
#     if value == 0:
#         try:
#             failed_runs[p_dict[str(key)]] +=1
#         except:
#             print("Missing pram file for", str(key))


open(path + "/speed_results.txt", "w").close()
with open(path + '/speed_results.txt', 'a') as my_file:
    my_file.write("Failed:\n")


print("\nFailed")

for key, value in fail_counter.items():
    print(key, len(value))
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

print("\nToo slow: ")
for key, value in slow_counter.items():
    print(key,len(value), value)
    with open(path + '/speed_results.txt', 'a') as my_file:
        my_file.write(str(key) + "," + str(len(value))+ "\n")