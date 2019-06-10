import numpy as np
import matplotlib.pyplot as plt
from glob import glob

path = "/home/maarten/Thesis_output/cpg_tuning/"
delta = 0.75
levels = 40
paths = glob(path + "*/")

X = np.loadtxt(paths[0] + "X.txt", delimiter=",")
Y = np.loadtxt(paths[0] + "Y.txt", delimiter=",")

# Create contour plots
fig, ax = plt.subplots()
for i in range(len(paths)):
    Z_ = np.loadtxt(paths[i] + "Z.txt", delimiter=",")
    my_max = np.max(Z_)*delta
    Z_ = Z_ > my_max
    cs = plt.contourf(X.tolist(),Y.tolist(),Z_.tolist(),extend = "both", corner_mask= False, cmap = "Greys", levels = 1, alpha = 0.125)

cs.changed()
plt.xlabel("Frequency factor")
plt.ylabel("Amplitude factor")
plt.savefig(path + "cpg_combined_grey_contour-top25.png")


paths = glob(path + "*/")
Z_shape = np.loadtxt(paths[0] + "Z.txt", delimiter=",").shape
Z = np.zeros(Z_shape)

# Get average
for i in range(len(paths)):
    Z_ = np.loadtxt(paths[i] + "Z.txt", delimiter=",")
    Z += Z_
Z /= 9.0

# Create plot
fig, ax = plt.subplots()
cs = plt.contourf(X.tolist(),Y.tolist(),Z.tolist(),extend = "both", cmap = "hot_r", levels = levels)
cs.changed()
fig.colorbar(cs)
plt.xlabel("Frequency factor")
plt.ylabel("Amplitude factor")
plt.savefig(path + "cpg_combined-" + str(levels) + ".png")
