from glob import glob
import os
import numpy as np
import matplotlib.pyplot as plt

finished = False
path = "/home/maarten/CLionProjects/revolve/output/cpg_bo/main_1560616625/"
path_list = glob(path + "/*/")
path_list = [path_ for path_ in path_list if os.path.isdir(path_)]
n_list = ["100", "250", "500","1000", "1501"]

name =path.split("-")[-1].split("/")[0].capitalize()
seen = []

# Group based on value of brain.
brain_number_dict = {}
brain_number_dict_inv = {}
for ix, path_ in enumerate(path_list):
    number = path_.split("/")[-2]
    subpaths = glob(path_ + "/*/")
    for subpath in subpaths:
        if os.path.isfile(subpath + "/" + "parameters.txt"):
            parameters = [(line.rstrip('\n')) for line in open(subpath + "/" + "parameters.txt")]
            for e in parameters:
                if "load_brain" in e:
                    brain_number = e.split("/")[-1].split("best_brain")[1].split(".")[0]
                    brain_number_dict_inv["/".join(subpath.split("/")[:-2]) +"/"] = brain_number
                    try:
                        if "/".join(subpath.split("/")[:-2]) not in brain_number_dict[brain_number]:
                            brain_number_dict[brain_number] += ["/".join(subpath.split("/")[:-2]) +"/"]
                    # Initiate entry if non-existent
                    except:
                        brain_number_dict[brain_number] = ["/".join(subpath.split("/")[:-2]) +"/"]

run_counter = {}
p_fitness = {}
fail_counter = {}
slow_counter = {}
brain_number_fitness = {}
for key, value in brain_number_dict.items():
    brain_number_fitness[str(key)] = []
    fail_counter[str(key)] = []
    slow_counter[str(key)] = []

# Walk through the paths.
for ix, path_ in enumerate(path_list):
    my_n = brain_number_dict_inv[path_]
    fin = False
    number = path_.split("/")[-2]
    run_counter[number] = 0
    subfolders = glob(path_ + "/*/")
    means = []

    # 1. Only consider folders that have a speed to object file and a dist_to_object file. These are successes
    subfolders_1 = []
    for subfolder in subfolders:
        if os.path.isfile(subfolder + "/speed_to_object.txt"):
            if os.path.isfile(subfolder + "/dist_to_object.txt"):
                subfolders_1 += [subfolder]

    # Check if we have subfolders
    if len(subfolders_1) == 0:
        fail_counter[my_n] += [number]
        print("Failed - 1", my_n)
        continue

    fail_counter_i = 0
    for subfolder in subfolders_1:
        if not fin:
            # get speeds and distances
            speeds = [(line.rstrip('\n')) for line in open(subfolder + "/speed_to_object.txt")][1:]
            dists  = [(line.rstrip('\n')) for line in open(subfolder + "/dist_to_object.txt")]

            # Prepare
            speed_list = []
            for e in speeds:
                speed = float(e.split(",")[-3])
                speed_list += [speed]

            if len(speed_list) == 0:
                continue

            # Check if we are fast enough
            if "0,0,1" in speeds or "0,0,3" in speeds or "0,0,5" in speeds or "0,0,7" in speeds or "0,0,9" in speeds or "0,0,11" in speeds or "0,0,13" in speeds or "0,0,15" in speeds:
                slow_counter[my_n] += [number]
                print("Too slow")
                # Succesful if here
                fin = True
                if number not in seen:
                    seen += [number]
                continue

            # Check if the run didn't fail
            if len(speeds) < 10:
                fail_counter_i +=1
                print("Failed - 2", )
                if len(subfolders_1) == fail_counter_i:
                    fail_counter[my_n] += [number]
                continue

            # Succesful if here
            fin = True

            # Get mean of each set of 4 samples
            my_mean = np.mean(speed_list)

            # Get brain number and save in the right brain
            brain_number_fitness[my_n] += [my_mean]

            if number not in seen:
                seen += [number]

print("\n\nFailed runs: ")
for key, value in fail_counter.items():
    print(key, len(value), value)
    with open(path + '/speed_results.txt', 'a') as my_file:
        my_file.write(str(key) + "," + str(value)+ "\n")

my_means = []
my_errors = []
print("\nFitness based on #values:")
for n_ in n_list:
    my_fitnesses = brain_number_fitness[n_]
    my_mean = np.mean(my_fitnesses)
    my_error = 1.96*np.std(my_fitnesses)/np.sqrt(len(my_fitnesses))
    my_means += [my_mean]
    my_errors += [my_error]
    print(n_, len(my_fitnesses))


print("\nToo slow: ")
for key, value in slow_counter.items():
    print(key,len(np.unique(np.array(value))), np.unique(np.array(value)))
    with open(path + '/speed_results.txt', 'a') as my_file:
        my_file.write(str(key) + "," + str(len(value))+ "\n")



not_seen = []
for i in range(150):
    if str(i) not in seen:
        not_seen += [i]

print("\nNot seen: ")
print(not_seen)

# Plot all at once
ax = plt.subplot()
plt.title(name + " speed 95% CI", fontsize = 20)
plt.xlabel("Learning time (evaluations)", fontsize = 20)
plt.ylabel("Speed to object (cm/s)", fontsize = 20)
plt.tick_params(labelsize=16)
plt.errorbar([i for i in range(len(my_means))],
             my_means,
             yerr = my_errors,
             linewidth =3.5,
             capsize = 6,
             capthick = 3.0,
             marker="o",
             ms = 10,
             ls = 'none')
ax.set_xticks([i for i in range(5)])
ax.set_xticklabels(["100","250", "500", "1000", "1500"])
plt.grid()
plt.tight_layout()

if finished:
    plt.savefig(path + name +"-exp3.pdf")
else:
    plt.show()