#!/usr/bin/env python3
import os
import sys

from pyrevolve import parser
from pyrevolve.util import Supervisor

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class OnlineEvolutionSupervisor(Supervisor):
    """
    Supervisor class that adds some output filtering for ODE errors
    """

    def __init__(self, *args, **kwargs):
        super(OnlineEvolutionSupervisor, self).__init__(*args, **kwargs)
        self.ode_errors = 0

    def write_stderr(self, data):
        """
        :param data:
        :return:
        """
        if 'ODE Message 3' in data:
            self.ode_errors += 1
        elif data.strip():
            sys.stderr.write(data)

        if self.ode_errors >= 100:
            self.ode_errors = 0
            sys.stderr.write('ODE Message 3 (100)\n')


if __name__ == "__main__":
    settings = parser.parse_args()
    supervisor = OnlineEvolutionSupervisor(
        manager_cmd='python3',
        # manager_args=['-u', os.path.join(here, "experiments/examples/manager.py")],
        manager_args=['-u', settings.manager],
        world_file=settings.world,
        simulator_cmd="gazebo",
        simulator_args=["--verbose"],
        plugins_dir_path=os.path.join(rvpath, 'build', 'lib'),
        models_dir_path=os.path.join(rvpath, 'models')
    )

    ret = supervisor.launch()
    # ret = supervisor.launch_simulator()
    sys.exit(ret)
