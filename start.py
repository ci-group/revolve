import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
rvpath = os.path.abspath(os.path.join(here, '..', 'revolve'))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from revolve.util import Supervisor

os.environ['GAZEBO_PLUGIN_PATH'] = os.path.join(rvpath, 'build')
os.environ['GAZEBO_MODEL_PATH'] = os.path.join(rvpath, 'worlds')

supervisor = Supervisor(
        manager_cmd=None,
        world_file="worlds/gait-learning.world",
        gazebo_cmd="gazebo",
)

supervisor.launch_gazebo()
