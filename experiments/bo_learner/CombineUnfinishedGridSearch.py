from glob import glob
import os

src_path = "/home/maarten/CLionProjects/revolve/output/cpg_bo/main_1557701167/"
paths = glob(src_path + "*/")
paths = [p for p in paths if "u-u" in p]


for experiment in paths:
    print(experiment)
    dst = experiment[:-4] + "/"
    print(dst)
    runs = glob(experiment + "/*")
    for run in runs:
        print(dst + run.split("/")[-1])
        os.rename(run, dst + run.split("/")[-1])
