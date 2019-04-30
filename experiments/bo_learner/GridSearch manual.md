
# Documentation

This GridSearch.py-file can be used to perform a grid search over some set of parameters. One can just call the file without arguments, e.g.:

`/home/maarten/projects/revolve-simulator/revolve/experiments/bo_learner/GridSearch.py`

# Parameters
After the imports, one can select parameters, e.g.:
```
# Parameters  
n_runs = 2  
n_jobs = 4  
my_yaml_path = "experiments/bo_learner/yaml/"  
base_model = "spider.yaml"  
manager = "experiments/bo_learner/manager.py"  
python_interpreter = "~/projects/revolve-simulator/revolve/.venv36/bin/python3.6"  
search_space = {
'init_method': ["RS", "LHS"],
'signal_factor': [1.5,1.7, 1.9, 2.1, 2.3],
}
```
  
What happens is that all the parameters in the yaml-file (my_yaml_path + base_model) are used as default for the manager, unless changed here. So, at `search_space` we declare that we want to iterate over the 'init_method' and 'signal_factor' parameters corresponding to the yaml-file. Note that this yaml-file will also contain what brain to use (from which it inherits the parameters). 

Search space parameters always need to be entered in a list (as we iterate over elements). From the search_space provided, we take every combination, and perform experiments for it. In this exapmle, we therefore have len(init_method)*len(signal_fator) = 10 experiments. Each experiment is repeated n_runs = 10 number of times, resulting in 200 runs (and with that 200 gzserver instances) to be performed.

The parameter n_jobs specifies the number of threads to be used. E.g. on the ripper we have 64 threads, so we can set n_jobs = 63 (advisable to not set the maximum). This is equivalanet to setting n_jobs = -2.

  
The output is written to `output/cpg_bo/main_<timestamp/`. In this directory, we get 1 sub-directory for each parameter setting. At the end of the script, the results of all parameter settings and n_runs reptitions, are combined into a plot, with as name the average final fitness. For instance, for parameter setting 0, we get fitness 0.01. This will be stored in `output/cpg_bo/main_1561111111/0/0.01.png`. In the `main_1561111111` directory, the results of the full experiments will be summarized in two text-files.

Some other advice:
 - Set verbose to [0] while running experiments to surpress output. Printing is expensive.
 - Make sure the variable python_interpreter points to the python interpreter you'd like to use, e.g.: python_interpreter = "~/projects/revolve/.venv/bin/python3.6". This python interpreter calls the ./revolve.py with themanager specified.