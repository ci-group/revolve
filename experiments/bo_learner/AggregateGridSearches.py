import matplotlib
from sys import platform
if platform == "darwin":
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from glob import glob
import numpy as np


# Parameters
path = "/home/maarten/Thesis_output/cpg_tuning/"
my_size_x = 11
my_size_y = 13
var1 = "range_ub"
var2 = "signal_factor"

paths = glob(path + "*/")
Z1 = np.loadtxt(paths[0] + "Z.txt", delimiter=",")
Z2 = np.loadtxt(paths[1] + "Z.txt", delimiter=",")
Z3 = np.loadtxt(paths[2] + "Z.txt", delimiter=",")
Z4 = np.loadtxt(paths[3] + "Z.txt", delimiter=",")
Z5 = np.loadtxt(paths[4] + "Z.txt", delimiter=",")
Z6 = np.loadtxt(paths[5] + "Z.txt", delimiter=",")
Z7 = np.loadtxt(paths[6] + "Z.txt", delimiter=",")
Z8 = np.loadtxt(paths[7] + "Z.txt", delimiter=",")
Z9 = np.loadtxt(paths[7] + "Z.txt", delimiter=",")
Z = (Z1 + Z2 + Z3 + Z4 + Z5 + Z6 + Z7 + Z8 + Z9)/9.0

X = np.loadtxt(paths[0] + "X.txt", delimiter=",")
Y = np.loadtxt(paths[0] + "Y.txt", delimiter=",")

# Create plot
fig, ax = plt.subplots()
cs = plt.contourf(X.tolist(),Y.tolist(),Z.tolist(),extend = "both", cmap = "hot_r", levels = 15)
cs.changed()
fig.colorbar(cs)
plt.xlabel(var1)
plt.ylabel(var2)
plt.savefig(path + "cpg_combined.png")

# Save XYZ
np.savetxt(path + "X.txt", np.matrix(X), fmt='%f', delimiter = ",")
np.savetxt(path + "Y.txt", np.matrix(Y), fmt='%f', delimiter = ",")
np.savetxt(path + "Z.txt", np.matrix(Z), fmt='%f', delimiter = ",")
