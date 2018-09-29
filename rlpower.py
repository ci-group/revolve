import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from revolve.util import Supervisor
# from revolve.tol.config import parser

if __name__ == "__main__":
    # args = parser.parse_args()

    supervisor = Supervisor(
            manager_cmd=os.path.join(here, "single_robot_manager.py"),
            world_file="worlds/gait-learning.world",
            gazebo_cmd="gazebo",
            gazebo_args=["--verbose"],
            plugins_dir_path=os.path.join(rvpath, 'build', 'lib'),
            models_dir_path=os.path.join(rvpath, 'models')
    )

    ret = supervisor.launch()
    sys.exit(ret)
