import matplotlib
from sys import platform
if platform == "darwin":
    matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from glob import glob
import pandas as pd
from mpl_toolkits import mplot3d
import numpy as np
import os
import plotly.offline as py
import plotly.graph_objs as go

# Parameters
path = "/home/maarten/Thesis_output/cpg_tuning/main_1557701167/"
var1 = "range_ub"
var2 = "signal_factor"
parameter_file = "parameters.txt"

# Set matplotlib font
font = {'size' : 18}
matplotlib.rc('font', **font)

# Get all sub-directories
path_list = glob(path + "*")
path_list = [path_ for path_ in path_list if os.path.isdir(path_)]
n_dirs = len(path_list)

# Holder
results = np.empty((n_dirs, 3))

# Check if it's numeric:
for ix, path_ in enumerate(path_list):
    try:
        int(path_.split("/")[-1] )
    except:
        continue

    # Cope with unsorted issue
    path_ =  "/".join(path_.split("/")[:-1]) + "/" + str(ix)

    # Get parameters for this file.
    subfolder_list = glob(path_ + "/*/")
    parameters = [(line.rstrip('\n')) for line in open(path_ + "/" + subfolder_list[0].split("/")[-2] +"/" + parameter_file)]
    for param in parameters:
        if(var1 in param):
            results[ix, 0] = float(param.split(":")[-1])
        if(var2 in param):
            results[ix, 1] = float(param.split(":")[-1])

    # Get Fitness. This is an average file in path_
    fitness = ".".join(glob(path_ + "/*.png")[0].split("/")[-1].split(".")[:-1])
    #fitness = ".".join(glob(path_ + "/*d.png")[0].split("/")[-1].split(".")[:-1])
    results[ix, 2] = fitness[:-1]

# Combine results
df = pd.DataFrame(results)
results = df.sort_values(by = [0,1]).to_numpy()

# Prepare for 3D plot
my_size_x = 11
my_size_y = 13
X =results[:,0].reshape((my_size_x,  my_size_y))
Y =results[:,1].reshape((my_size_x,  my_size_y))
Z =results[:,2].reshape((my_size_x,  my_size_y))


X = np.loadtxt(path + "X.txt", delimiter=",").reshape((my_size_x,  my_size_y))
Y = np.loadtxt(path + "Y.txt", delimiter=",").reshape((my_size_x,  my_size_y))
Z = np.loadtxt(path + "Z.txt", delimiter=",").reshape((my_size_x,  my_size_y)) - 0.05

# Verbose
for i in range(my_size_x):
    for j in range(my_size_y):
        print(X[i,j], Y[i,j], Z[i,j])

# # Construct 3D plot
# fig = plt.figure(figsize=(10,10))
# ax = plt.axes(projection='3d')
# ax.plot_wireframe(X, Y, Z, rstride=1, cstride=1,
#                cmap='viridis', edgecolor='none')
# ax.set_xlabel(var1)
# ax.set_ylabel(var2)
# ax.set_zlabel("fitness")
# plt.savefig(path + "3Dplot.png")


# Create plot
levels = 40
fig, ax = plt.subplots()
cs = plt.contourf(X.tolist(),Y.tolist(),Z.tolist(),extend = "both", cmap = "hot_r", levels = levels)
#cs = plt.contourf(X,Y,Z,extend = "both", cmap = "hot_r", levels = levels)
cs.changed()
fig.colorbar(cs)
plt.xlabel("Frequency factor")
plt.ylabel("Amplitude factor")
plt.title("Gecko12")
plt.tight_layout()
plt.savefig(path + "/gecko12-contour" + str(levels) + ".png")
#plt.show()

# Get data for plotly
data = [
    go.Surface(
        x = X,
        y = Y,
        z = Z
    )
]

# # Layout
# layout = go.Layout(
#     title = path,
#     scene = dict(
#         xaxis=dict(title=var1),
#         yaxis=dict(title=var2),
#         zaxis=dict(title="fitness"),
#     ),
# )

# Construct ploty
#fig = go.Figure(data=data)
#py.plot(fig, filename=path + "interactive_3d")
#print(len(X), len(Y), len(Z))
