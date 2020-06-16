from glob import glob
import os

python_interpreter = "/Users/lan/projects/revolve/venv/bin/python"
path = "/Users/lan/projects/revolve/output/cpg_bo/main_1557477606/47/"


paths = glob(path + "*/")
print(len(paths))
paths = [p for p in paths if os.path.isfile(p + "fitnesses.txt")]
print(len(paths))

for path in paths:
    # Call the experiment
    py_command = python_interpreter + " experiments/bo_learner/RunAnalysisBO.py " + path + "/ 50 1"
    os.system(py_command)