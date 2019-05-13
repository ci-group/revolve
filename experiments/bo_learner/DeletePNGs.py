from glob import glob
import os

python_interpreter = "/home/maarten/CLionProjects/revolve/venv/bin/python"
path = "/home/maarten/CLionProjects/revolve/output/cpg_bo/main_1557046999/"


paths = glob(path + "*/*.png")
print(len(paths))

for path in paths:
    os.remove(path)
