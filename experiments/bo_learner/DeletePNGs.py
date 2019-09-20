from glob import glob
import os

path = "/home/gongjinlan/projects/revolve/output/cpg_bo/main_1559644358-BO-gecko7/"
print(path)

paths = glob(path + "*/*.png")
print(len(paths))

for path in paths:
    os.remove(path)
