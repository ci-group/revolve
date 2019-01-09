#!/usr/bin/env python3
import os
import sys
import argparse

from pyrevolve import parser
from pyrevolve.util import VREPSupervisor

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


if __name__ == "__main__":
    settings = parser.parse_args()
    supervisor = VREPSupervisor(
        manager_cmd='python3',
        # manager_args=['-u', os.path.join(here, "experiments/examples/manager.py")],
        manager_args=['-u', settings.manager],
        world_file=settings.world,
        simulator_cmd="vrep",
        simulator_args=None,
        vrep_folder="/usr/share/vrep/",
        plugins_dir_path=os.path.join(rvpath, 'build', 'lib'),
        models_dir_path=os.path.join(rvpath, 'models')
    )

    ret = supervisor.launch()
    sys.exit(ret)
