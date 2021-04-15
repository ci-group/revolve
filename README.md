<img  align="right" width="150" height="150"  src="/docs/revolve-logo.png">

**Revolve** is an open source software framework for robot evolution providing C++ and Python libraries to create,
simulate and manage robots in the Gazebo general-purpose robot simulator. Given a specification, a robot body can be constructed by Revolve from a tree structure, starting with a root node extending to other body parts through its attachment slots. Revolve also ships with some simple generator classes, which can generate arbitrary robot bodies from scratch given a set of constraints.

Revolve was originally developed and is maintained by researchers and engineers working at the Computational Intelligence Group within Vrije Universiteit Amsterdam for the purposes of conducting robot body and brain evolutionary-related research. The system is general enough to be applicable in a wide variety of other domains, as well.

## Installation

The current system is supported for Linux and Mac OS X platforms.
If all [pre-requirements](https://github.com/ci-group/revolve/wiki/Installation-Instructions-for-Gazebo) are satisfied, to install J Lo's learning branch:


```bash
git clone https://github.com/ci-group/revolve.git --recursive -b experiments/jlo_learning
export SIM_HOME=`pwd` && cd $SIM_HOME/revolve
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE="Release"
make -j8
```

```bash
cd $SIM_HOME/revolve
mkdir cmake-build-multineat
cd cmake-build-multineat
cmake ../thirdparty/MultiNEAT -DCMAKE_BUILD_TYPE="Release"
make -j8
make install
```

Within the `revolve/` root directory create Python virtual environment(change v3.9 to your own python version) :

```bash
cd $SIM_HOME/revolve
virtualenv --python python3.9 .venv
source .venv/bin/activate
pip install -r requirements.txt
```

To verify the build, run following command to open the Gazebo simulator:
```bash
(.venv) ./revolve.py --simulator-cmd=gazebo
```
If you want to have an overview of all possible Revolve commands, run `./revolve.py --help`.

*See [Installation Instructions for Revolve](https://github.com/ci-group/revolve/wiki/Installation-Instructions-for-Revolve)
for detailed instructions, and how to build from source.*

#### *To run the evolution_learning experiment*
```bash
cd $SIM_HOME/revolve
source .venv/bin/activate
(.venv) ./revolve.py --simulator-cmd=gazebo --manager=experiments/learner_knn/manager_pop.py
```
#### *Parameters you may want to change for your own experiment*
* In experiments/learner_knn/manager_pop.py, you can change the experiment params, such as num_generations, population_size and offspring_size.
* In pyrevolve/revolve_bot/brain/cpg.py, you can change the the number of the learning trials (n_learning_iterations).
* In pyrevolve/util/supervisor/simulator_queue.py, you can change the evaluation timeout in the simulator queue (EVALUATION_TIMEOUT).

#### *To run the evolution_only experiment* Switch to the main branch
```bash
git checkout master
cd $SIM_HOME/revolve
source .venv/bin/activate
(.venv) ./revolve.py --simulator-cmd=gazebo --manager=experiments/examples/manager_pop.py
```

## For more information

* [EvoSphere Website](https://evosphere.eu/)
* [CIGroup Website](https://www.cs.vu.nl/ci/)

## License

[Apache License 2.0](LICENSE)
