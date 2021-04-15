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

#### *To run the evolution_only experiment*
cd $SIM_HOME/revolve
source .venv/bin/activate
(.venv) ./revolve.py --simulator-cmd=gazebo --manager=experiments/examples/manager_pop.py

#### *To run the evolution_learning experiment*
cd $SIM_HOME/revolve
source .venv/bin/activate
(.venv) ./revolve.py --simulator-cmd=gazebo --manager=experiments/learner_knn/manager_pop.py

## Contribution guidelines

If you want to contribute to Revolve, be sure to review the [contribution
guidelines](CONTRIBUTING.md). By participating, you are expected to
uphold this code.

We use [GitHub issues](https://github.com/ci-group/revolve/issues) for
tracking requests and bugs.

The Revolve project strives to abide by generally accepted best practices in open-source software development:
[![CII Best Practices](https://bestpractices.coreinfrastructure.org/projects/2520/badge)](https://bestpractices.coreinfrastructure.org/projects/2520)
[![CircleCI](https://circleci.com/gh/ci-group/revolve.svg?style=svg)](https://circleci.com/gh/ci-group/revolve)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/5443e24ddd4d413b897206b546d5600e)](https://www.codacy.com/app/ci-group/revolve?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ci-group/revolve/&amp;utm_campaign=Badge_Grade)

## Contributors

We would like to thank all contributors of Revolve project!

Special thanks to [Elte Hupkes](https://github.com/ElteHupkes/) who designed the codebase and professor [Gusz Eiben](https://www.cs.vu.nl/~gusz/) whose energy is pushing the project forward.
Many thanks to [Milan Jelisavcic](https://github.com/milanjelisavcic/) and [Matteo De Carlo](https://github.com/portaloffreedom/) for redesigning and simplifying the codebase.
For the complete list of contributors see [AUTHORS](AUTHORS).

## For more information

* [EvoSphere Website](https://evosphere.eu/)
* [CIGroup Website](https://www.cs.vu.nl/ci/)

## License

[Apache License 2.0](LICENSE)
