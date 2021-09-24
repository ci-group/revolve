import copy
from typing import Iterable, Optional

import numpy as np

from pyrevolve.SDF.math import Vector3, Quaternion
from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.util import Time
from pyrevolve.util.supervisor.rabbits import RobotState, RobotEvaluation, PostgreSQLDatabase
from pyrevolve.angle.manage.robotmanager import RobotManager as RvRobotManager


class DBRobotManager(RvRobotManager):
    def __init__(self, db: PostgreSQLDatabase,
                 robot_id: int,
                 robot: RevolveBot,
                 battery_level: float = 0.0,
                 evaluation_time: Optional[float] = None,
                 warmup_time: float = 0.0):
        super().__init__(robot=robot,
                         position=Vector3(),
                         time=Time(),
                         battery_level=battery_level,
                         speed_window=60,
                         warmup_time=warmup_time)
        self._dist = 0.
        self._time = 0.
        self._positions = []
        self._times = []
        self._orientations = []
        self._contacts = []
        self.starting_position = None
        self.starting_time = None

        with db.session() as session:
            last_eval: RobotEvaluation = session \
                .query(RobotEvaluation) \
                .filter(RobotEvaluation.robot_id == int(robot_id)) \
                .order_by(RobotEvaluation.n.desc()) \
                .one()
            last_eval_n = last_eval.n

            # behaviour = [s for s in session.query(RobotState).filter(RobotState.evaluation_robot_id == robot_id)]
            behaviour_query: Iterable[RobotState] = session \
                .query(RobotState) \
                .filter(RobotState.evaluation == last_eval) \
                .order_by(RobotState.time_sec.asc()) \
                .order_by(RobotState.time_nsec.asc())

            # TODO filter out grace time from the query directly
            # TODO sort query by time

            previous_pos = None
            previous_time = None
            robot_start_time: Optional[Time] = None
            for state in behaviour_query:
                state: RobotState = state
                time: Time = Time(sec=state.time_sec, nsec=state.time_nsec)
                if robot_start_time is None:
                    robot_start_time = time

                world_time: float = float(time - robot_start_time)
                if world_time < warmup_time:
                    # skip grace time states
                    continue

                if world_time > (evaluation_time+warmup_time):
                    # skip the remaining evaluations, we only care about the first N seconds of lifetime
                    break

                position: Vector3 = Vector3(state.pos_x, state.pos_y, state.pos_z)
                quaternion = Quaternion(state.rot_quaternion_w,
                                        state.rot_quaternion_x,
                                        state.rot_quaternion_y,
                                        state.rot_quaternion_z)
                euler = quaternion.get_rpy()
                euler = np.array([euler[0], euler[1], euler[2]])  # roll / pitch / yaw

                self._positions.append(position)
                self._times.append(time)
                self._orientations.append(euler)
                self._orientation_vecs.append(None)  # TODO
                self._contacts.append(0)  # TODO
                self._seconds.append(None)  # TODO

                self.last_position = position.copy()
                self.last_update = time

                if self.starting_position is None:
                    self.starting_time = time
                    self.starting_position = position.copy()
                else:
                    ds: float = np.sqrt((position.x - previous_pos.x)**2 + (position.y - previous_pos.y)**2)
                    dt: float = float(time - previous_time)
                    self._dist += ds
                    self._time += dt

                    if len(self._dt) >= self.speed_window:
                        # Subtract oldest values if we're about to override it
                        self._dist -= self._ds[0]
                        self._time -= self._dt[0]

                    self._ds.append(ds)
                    self._dt.append(dt)

                previous_pos = position.copy()
                previous_time = copy.deepcopy(time)

            assert abs(float(time - self.starting_time) - evaluation_time) < 0.5
