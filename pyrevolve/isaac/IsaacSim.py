"""
Isaac Simulator wrapper for functionality
"""
from typing import AnyStr, List, Optional, Union, Dict, Callable

import math
import numpy as np
from isaacgym import gymapi

from pyrevolve.revolve_bot.brain.controller import Controller as RevolveController
from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase
from . import isaac_logger
from .ISAACBot import ISAACBot


class IsaacSim:
    _gym: gymapi.Gym
    _sim: gymapi.Sim
    _viewer: Optional[gymapi.Viewer]
    _asset_root: AnyStr
    _db: Optional[PostgreSQLDatabase]
    _spacing: float
    build_environments: Optional[Callable[[gymapi.Gym, gymapi.Sim, gymapi.Vec3, gymapi.Vec3, int, gymapi.Env], None]]
    robots: List[ISAACBot]
    robot_handles: List[int]
    envs: List[gymapi.Env]
    _env_lower: gymapi.Vec3
    _env_upper: gymapi.Vec3
    _num_per_row: int
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
                 environment_constructor: Optional[Callable[[gymapi.Gym, gymapi.Sim, gymapi.Vec3, gymapi.Vec3, int, gymapi.Env], None]] = None,
                 ):
        self._asset_root = asset_root
        self._db = db
        self._spacing = environment_size
        self.build_environment = environment_constructor
        self.robot_handles = []
        self.envs = []
        self.robots = []

        self._gym = gymapi.acquire_gym()
        self._sim = self._gym.create_sim(compute_device_id,
                                         graphic_device_id,
                                         physics_engine,
                                         sim_params)
        if self._sim is None:
            isaac_logger.error("*** Failed to create sim ***")
            raise RuntimeError("Failed to create sim")

        # Create environments
        self._env_lower = gymapi.Vec3(-environment_size, 0.0, -environment_size)
        self._env_upper = gymapi.Vec3(environment_size, environment_size, environment_size)
        self._num_per_row = int(math.sqrt(num_envs))
        for i in range(num_envs):
            # You should initialize these at the last minute because of performance reasons
            # env = self._gym.create_env(self._sim, env_lower, env_upper, num_per_row)
            self.envs.append(None)

        self._viewer = None
        if not headless:
            self._viewer = self._gym.create_viewer(self._sim, gymapi.CameraProperties())
            # Point camera at environments
            cam_pos = gymapi.Vec3(self._num_per_row/2, -4.0, 4.0)
            cam_target = gymapi.Vec3(self._num_per_row/2, self._num_per_row/2, 0)
            self._gym.viewer_camera_look_at(self._viewer, None, cam_pos, cam_target)

    def is_headless(self):
        return self._viewer is None

    def add_ground(self, plane_params: Optional[gymapi.PlaneParams] = None) -> None:
        if plane_params is None:
            plane_params = gymapi.PlaneParams()
        self._gym.add_ground(self._sim, plane_params)

    def insert_robot(self,
                     env: Union[gymapi.Env, int],
                     robot: ISAACBot,
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
        :param robot: Robot to insert
        :param urdf_path: path to the robot asset (URDF)
        :param robot_asset_options: robot asset simulator parameters
        :param pose: transform of where the robot will be initially placed
        :param robot_name: name of the robot
        :param group: collision group
        :param filter_: bitwise filter for elements in the same collisionGroup
        :param segmentation_id: segmentation ID used in segmentation camera sensor
        :return: robot handle
        """
        # TODO wait for Nvidia to allow us to insert the robot in a running simulation
        env_i, env = self._environment(env)
        robot.env_index = env_i
        self.robots.append(robot)

        robot_asset = self._gym.load_urdf(self._sim, self._asset_root, urdf_path, robot_asset_options)

        # calculate correct z height
        robot.handle = self._gym.create_actor(env, robot_asset, pose, robot_name, group, filter_, segmentation_id)
        self.robot_handles.append(robot.handle)

        body_states = self._gym.get_actor_rigid_body_states(
            env, robot.handle, gymapi.STATE_ALL)
        min_z = np.min(body_states["pose"]['p']['z'])

        pose.p.z -= (min_z - 0.08)  # 0.08m (8cm) it's an estimated half max-size of all modules
        # WARNING: we are passing an actor handle as a rigid body handle, things may not work properly
        self._gym.set_rigid_transform(env, robot.handle, pose)

        # Robot Actor properties
        props = self._gym.get_actor_dof_properties(env, robot.handle)
        props["driveMode"].fill(gymapi.DOF_MODE_POS)
        props["stiffness"].fill(1000.0)
        props["damping"].fill(600.0)
        self._gym.set_actor_dof_properties(env, robot.handle, props)

        robot.create_actuator_map(self._gym.get_actor_dof_dict(env, robot.handle))

        robot.born_time = self.get_sim_time()

        return robot.handle

    def insert_obj(self,
                   env: Union[gymapi.Env, int],
                   obj_asset,
                   pose: gymapi.Transform,
                   name: Optional[AnyStr] = None,
                   collision_group: int = - 1,
                   filter_: int = - 1,
                   segmentation_id: int = 0) -> int:
        """
        Inserts a robot in the system
        :param env: Environmental Handle
        :param obj_asset: Asset to insert
        :param pose: transform of where the robot will be initially placed
        :param name: optional name for the object
        :param collision_group: collision group
        :param filter_: bitwise filter for elements in the same collisionGroup
        :param segmentation_id: segmentation ID used in segmentation camera sensor
        :return: robot handle
        """
        # TODO wait for Nvidia to allow us to insert the robot in a running simulation
        env_i, env = self._environment(env)
        handle = self._gym.create_actor(env, obj_asset, pose, name, collision_group, filter_, segmentation_id)
        return handle

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
        env_i, env = self._environment(env)
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
        env_i, env = self._environment(env)
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

    def _environment(self, env: Union[int, gymapi.Env]) -> (int, gymapi.Env):
        if isinstance(env, int):
            index: int = env
            env = self.envs[index]
            if env is None:
                env = self._gym.create_env(self._sim, self._env_lower, self._env_upper, self._num_per_row)
                if callable(self.build_environment):
                    self.build_environment(self._gym, self._sim, self._env_lower, self._env_upper, self._num_per_row, env)
                self.envs[index] = env
        else:
            index: int = self.envs.index(env)

        if not isinstance(env, gymapi.Env):
            raise RuntimeError("Wrong argument passed to function")
        return index, env

    def update_robots(self, time: float, delta: float) -> None:
        if len(self.robots) == 0:
            return
        if self._db is None:
            for robot in self.robots:
                robot.update_robot(time, delta, self)
        else:
            with self._db.session() as robot_states_session:
                for robot in self.robots:
                    robot.update_robot(time, delta, self, robot_states_session)
                robot_states_session.commit()
