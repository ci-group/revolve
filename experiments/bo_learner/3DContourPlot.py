import numpy as np
import matplotlib.pyplot as plt
from glob import glob

path = "/home/maarten/Thesis_output/cpg_tuning/"
delta = 0.75
var1 = "range_ub"
var2 = "signal_factor"
paths = glob(path + "*/")

X = np.loadtxt(paths[0] + "X.txt", delimiter=",")
Y = np.loadtxt(paths[0] + "Y.txt", delimiter=",")

fig, ax = plt.subplots()

for i in range(len(paths)):
    Z_ = np.loadtxt(paths[i] + "Z.txt", delimiter=",")
    my_max = np.max(Z_)*delta
    Z_ = Z_ > my_max
    cs = plt.contourf(X.tolist(),Y.tolist(),Z_.tolist(),extend = "both", cmap = "Greys", levels = 1, alpha = 0.125)

cs.changed()

plt.xlabel(var1)
plt.ylabel(var2)
plt.show()
plt.savefig(path + "cpg_combined_grey_contour-top25.png")
