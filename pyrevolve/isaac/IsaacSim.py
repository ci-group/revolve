"""
Isaac Simulator wrapper for functionality
"""
import math
from typing import AnyStr, List, Optional, Union, Dict

from isaacgym import gymapi

from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase
from pyrevolve.revolve_bot.brain.controller import Controller as RevolveController
from . import isaac_logger
from .ISAACBot import ISAACBot


class IsaacSim:
    _gym: gymapi.Gym
    _sim: gymapi.Sim
    _viewer: Optional[gymapi.Viewer]
    _asset_root: AnyStr
    _db: PostgreSQLDatabase
    robot_handles: List[int]
    envs: List[gymapi.Env]
    controllers: Dict[int, RevolveController]

    def __init__(self,
                 db: PostgreSQLDatabase,
                 asset_root: AnyStr,
                 compute_device_id: int,
                 graphic_device_id: int,
                 physics_engine: gymapi.SimType,
                 sim_params: gymapi.SimParams,
                 headless: bool,
                 num_envs: int,
                 environment_size: float = 2.0,
                 ):
        self._asset_root = asset_root
        self._db = db
        self.robot_handles = []
        self.envs = []

        self._gym = gymapi.acquire_gym()
        self._sim = self._gym.create_sim(compute_device_id,
                                         graphic_device_id,
                                         physics_engine,
                                         sim_params)
        if self._sim is None:
            isaac_logger.error("*** Failed to create sim ***")
            raise RuntimeError("Failed to create sim")

        self._viewer = None
        if not headless:
            self._viewer = self._gym.create_viewer(self._sim, gymapi.CameraProperties())
            # Point camera at environments
            cam_pos = gymapi.Vec3(-4.0, 4.0, -1.0)
            cam_target = gymapi.Vec3(0.0, 2.0, 1.0)
            self._gym.viewer_camera_look_at(self._viewer, None, cam_pos, cam_target)

        # Create environments
        env_lower = gymapi.Vec3(-environment_size, 0.0, -environment_size)
        env_upper = gymapi.Vec3(environment_size, environment_size, environment_size)
        num_per_row = int(math.sqrt(num_envs))
        for i in range(num_envs):
            env = self._gym.create_env(self._sim, env_lower, env_upper, num_per_row)
            self.envs.append(env)

    def add_ground(self, plane_params: Optional[gymapi.PlaneParams] = None) -> None:
        if plane_params is None:
            plane_params = gymapi.PlaneParams()
        self._gym.add_ground(self._sim, plane_params)

    def insert_robot(self,
                     env: Union[gymapi.Env, int],
                     urdf_path: AnyStr,
                     robot_asset_options: gymapi.AssetOptions,
                     pose: gymapi.Transform,
                     robot_name: AnyStr,
                     group: int = - 1,
                     filter_: int = - 1,
                     segmentation_id: int = 0) -> int:
        """
        Inserts a robot in the system
        :param env: Environmental Handle
        :param urdf_path: path to the robot asset (URDF)
        :param robot_asset_options: robot asset simulator parameters
        :param pose: transform of where the robot will be initally placed
        :param robot_name: name of the robot
        :param group: collision group
        :param filter_: bitwise filter for elements in the same collisionGroup
        :param segmentation_id: segmentation ID used in segmentation camera sensor
        :return: robot handle
        """
        env: gymapi.Env = self._environment(env)
        robot_asset = self._gym.load_urdf(self._sim, self._asset_root, urdf_path, robot_asset_options)
        robot_handle: int = self._gym.create_actor(env, robot_asset, pose, robot_name, group, filter_, segmentation_id)
        self.robot_handles.append(robot_handle)
        props = self._gym.get_actor_dof_properties(env, robot_handle)
        props["driveMode"].fill(gymapi.DOF_MODE_POS)
        props["stiffness"].fill(1000.0)
        props["damping"].fill(600.0)
        self._gym.set_actor_dof_properties(env, robot_handle, props)
        return robot_handle

    def add_controller(self, robot_handle: int, controller: RevolveController):
        self.controllers[robot_handle] = controller

    def prepare(self) -> bool:
        return self._gym.prepare_sim(self._sim)

    def simulate(self) -> None:
        self._gym.simulate(self._sim)

    def fetch_results(self, wait_for_latest_sim_step: bool) -> None:
        self._gym.fetch_results(self._sim, wait_for_latest_sim_step)

    def set_robot_dof_position_targets(self,
                                       env: Union[int, gymapi.Env],
                                       robot_handle: int,
                                       position_target: List[float],
                                       ) -> None:
        env: gymapi.Env = self._environment(env)
        self._gym.set_actor_dof_position_targets(env, robot_handle, position_target)

    def get_robot_position_rotation(self,
                                    env: Union[int, gymapi.Env],
                                    robot_handle: int,
                                    ) -> (gymapi.Vec3, gymapi.Quat):
        """
        Returns last available data for position and rotation of a robot (static body)
        :param env: environement were to find the robot
        :param robot_handle: handle of the robot
        :return: Position and Rotation of the robot
        """
        env: gymapi.Env = self._environment(env)
        robot_pose = self._gym.get_actor_rigid_body_states(env, robot_handle, gymapi.STATE_POS)["pose"]
        robot_pos: gymapi.Vec3 = robot_pose['p'][0]  # -> [0] is to get the position of the head
        robot_rot: gymapi.Quat = robot_pose['r'][0]  # -> [0] is to get the rotation of the head
        return robot_pos, robot_rot

    def step_graphics(self) -> None:
        self._gym.step_graphics(self._sim)

    def draw_viewer(self, render_collision: bool = False) -> None:
        if self._viewer is not None:
            self._gym.draw_viewer(self._viewer, self._sim, render_collision)

    def sync_frame_time(self) -> None:
        """
        Makes the simulator run in real time
        """
        self._gym.sync_frame_time(self._sim)

    def get_sim_time(self) -> float:
        return self._gym.get_sim_time(self._sim)

    def destroy(self) -> None:
        # destroy camera sensors here, if any
        # destroy performance timers here, if any
        for env in self.envs:
            self._gym.destroy_env(env)
        if self._viewer is not None:
            self._gym.destroy_viewer(self._viewer)
        self._gym.destroy_sim(self._sim)

    def _environment(self, env: Union[int, gymapi.Env]) -> gymapi.Env:
        if isinstance(env, int):
            env = self.envs[env]

        if not isinstance(env, gymapi.Env):
            raise RuntimeError("Wrong argument passed to function")
        return env
