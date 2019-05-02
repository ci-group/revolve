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

        if self.ode_errors >= 1000:
            self.ode_errors = 0
            sys.stderr.write('ODE Message 3 (1000)\n')


if __name__ == "__main__":
    settings = parser.parse_args()
    manager_settings = sys.argv[1:]
    supervisor = OnlineEvolutionSupervisor(
        manager_cmd=settings.manager,
        manager_args=manager_settings,
        world_file=settings.world,
        simulator_cmd=settings.simulator_cmd,
        simulator_args=["--verbose"],
        plugins_dir_path=os.path.join(rvpath, 'build', 'lib'),
        models_dir_path=os.path.join(rvpath, 'models')
    )

    if settings.manager is None:
        ret = supervisor.launch_simulator()
    else:
        ret = supervisor.launch()
    sys.exit(ret)
