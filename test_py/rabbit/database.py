import unittest
from typing import List

from sqlalchemy.orm import Session

from pyrevolve.util.supervisor.rabbits import PostgreSQLDatabase
from pyrevolve.util.supervisor.rabbits import Robot, RobotEvaluation, RobotState


class TestDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self.db = PostgreSQLDatabase()
        self.db.start_sync()
        self.db.destroy()
        self.db.init_db(first_time=False)

    def tearDown(self) -> None:
        self.db.disconnect()
        self.assertEqual(self.db.destroy(), True)
        self.db = None

    def test_session(self) -> None:
        with self.db.session() as session:
            self.assertEqual(session.is_active, True)

        session2: Session = self.db.session()
        self.assertEqual(session2.is_active, True)
        session2.close()

    @staticmethod
    def _generate_robot_states(n: int, eval: RobotEvaluation):
        for i in range(n):
            yield RobotState(evaluation=eval, time_sec=i, time_nsec=0,
                             pos_x=i, pos_y=i*20, pos_z=i,
                             rot_quaternion_x=i, rot_quaternion_y=i,rot_quaternion_z=i, rot_quaternion_w=i,
                             orientation_left=i, orientation_right=i, orientation_forward=i, orientation_back=i)

    def test_insert(self) -> None:
        with self.db.session() as session:
            new_robot = Robot(name="spider_example")
            session.add(new_robot)
            new_eval = RobotEvaluation(robot=new_robot, n=1, fitness=0.1)
            session.add(new_eval)
            new_eval2 = RobotEvaluation(robot=new_robot, n=2, fitness=1.1)
            session.add(new_eval2)
            session.commit()
            self.assertEqual(1, new_robot.id)
        self.assertEqual(1, new_robot.id)

        with self.db.session() as session:
            for state in TestDatabase._generate_robot_states(10, new_eval):
                session.add(state)
            for state in TestDatabase._generate_robot_states(5, new_eval2):
                session.add(state)
            session.commit()

    def test_read(self) -> None:
        self.test_insert()

        with self.db.session() as session:
            robot = session.query(Robot).one()

            evaluations = [evaluation for evaluation in session.query(RobotEvaluation)]
            self.assertEqual(len(evaluations), 2)
            self.assertEqual(evaluations[0].robot.name, robot.name)
            self.assertEqual(evaluations[1].robot.name, robot.name)
            self.assertEqual(evaluations[0].n, 1)
            self.assertEqual(evaluations[1].n, 2)
            self.assertEqual(evaluations[0].fitness, 0.1)
            self.assertEqual(evaluations[1].fitness, 1.1)

            first_eval: RobotEvaluation = session.query(RobotEvaluation).first()
            self.assertEqual(first_eval, evaluations[0])
            last_eval = list(session.query(RobotEvaluation))[-1]
            self.assertEqual(last_eval, evaluations[1])

            states: List[RobotState] = [s for s in session.query(RobotState)]
            self.assertEqual(len(states), 15)
            for s in states:
                self.assertEqual(s.robot.name, robot.name)
                self.assertEqual(s.time_nsec, 0)

            states1: List[RobotState] = [s for s in session.query(RobotState).filter(RobotState.evaluation == first_eval)]
            self.assertEqual(len(states1), 10)
            for i, s in enumerate(states1):
                self.assertEqual(s.robot.name, robot.name)
                self.assertEqual(s.evaluation.n, 1)
                self.assertEqual(s.time_sec, i)
                self.assertEqual(s.pos_x, i)
                self.assertEqual(s.pos_y, i*20)
                self.assertEqual(s.pos_z, i)
                self.assertEqual(s.rot_quaternion_x, i)
                self.assertEqual(s.rot_quaternion_y, i)
                self.assertEqual(s.rot_quaternion_z, i)
                self.assertEqual(s.rot_quaternion_w, i)
                self.assertEqual(s.orientation_forward, i)
                self.assertEqual(s.orientation_back, i)
                self.assertEqual(s.orientation_left, i)
                self.assertEqual(s.orientation_right, i)

            states2 = [s for s in session.query(RobotState).filter(RobotState.evaluation == last_eval)]
            self.assertEqual(len(states2), 5)
            for i, s in enumerate(states2):
                self.assertEqual(s.robot.name, robot.name)
                self.assertEqual(s.evaluation.n, 2)
                self.assertEqual(s.time_sec, i)
                self.assertEqual(s.pos_x, i)
                self.assertEqual(s.pos_y, i*20)
                self.assertEqual(s.pos_z, i)
                self.assertEqual(s.rot_quaternion_x, i)
                self.assertEqual(s.rot_quaternion_y, i)
                self.assertEqual(s.rot_quaternion_z, i)
                self.assertEqual(s.rot_quaternion_w, i)
                self.assertEqual(s.orientation_forward, i)
                self.assertEqual(s.orientation_back, i)
                self.assertEqual(s.orientation_left, i)
                self.assertEqual(s.orientation_right, i)

            states_robots: List[RobotState] = [s for s in session.query(RobotState).filter(RobotState.robot == robot)]
            self.assertListEqual(states, states_robots)
