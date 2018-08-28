import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from revolve.util import Supervisor

if __name__ == "__main__":

    supervisor = Supervisor(
        manager_cmd=None,
        world_file="worlds/gait-learning.world",
        gazebo_cmd="gazebo",
        gazebo_args=["--verbose"],
        plugins_dir_path=os.path.join(rvpath, 'build', 'lib'),
        models_dir_path=os.path.join(rvpath, 'models')
    )

    ret = supervisor.launch_gazebo()
    sys.exit(ret)
