import matplotlib
from sys import platform
if platform == "darwin":
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from glob import glob
import numpy as np
from mpl_toolkits import mplot3d


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
Z = (Z1 + Z2 + Z3 + Z4)/4

X = np.loadtxt(paths[0] + "X.txt", delimiter=",")
Y = np.loadtxt(paths[0] + "Y.txt", delimiter=",")


print(X,Y,Z)
print(type(X), type(Y), type(Z))
# Construct 3D plot
fig = plt.figure(figsize=(10,10))
ax = plt.axes(projection='3d')
ax.plot_wireframe(Z1, Z1, Z1, rstride=1, cstride=1,
                  cmap='viridis', edgecolor='none')
ax.set_xlabel(var1)
ax.set_ylabel(var2)
ax.set_zlabel("fitness")
plt.gca()
plt.gcf()
plt.show()
#plt.savefig(path + "3Dplot.png")

plt.plot(X,Y)