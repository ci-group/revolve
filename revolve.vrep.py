#!/usr/bin/env python3
import os
import sys
import argparse

from revolve.util import VREPSupervisor

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='''
    Revolve supervisor manager (VREP Version)
    ''')

    default_manager = os.path.join(here, "examples", "manager.py") 
    parser.add_argument('--manager', type=str,
        default=default_manager,
        help="Which manager to use, default to {}".format(default_manager))

    args = parser.parse_args()

    supervisor = VREPSupervisor(
        manager_cmd='python3',
        manager_args=['-u', args.manager],
        world_file="worlds/gait-learning.world",
        vrep_cmd="vrep",
        vrep_args=None,
        vrep_folder="/usr/share/vrep/",
        plugins_dir_path=os.path.join(rvpath, 'build', 'lib'),
        models_dir_path=os.path.join(rvpath, 'models')
    )

    ret = supervisor.launch()
    sys.exit(ret)
