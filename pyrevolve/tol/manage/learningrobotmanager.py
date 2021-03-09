from pyrevolve.util import Time
from pyrevolve.SDF.math import Vector3, Quaternion
from pyrevolve.spec.msgs.robot_states_learning_pb2 import LearningRobotStates, BehaviourData


class Evaluation:
    def __init__(self, eval_n: int, fitness: float, behaviour: list):
        """
        :param eval_n:
        :param fitness:
        :param behaviour:
        :type behaviour: list(BehaviourData)
        """
        self.eval_n = eval_n
        self.fitness = fitness
        self.behaviour_data = behaviour

    def times(self):
        return [Time(data.time.sec, data.time.nsec) for data in self.behaviour_data]

    def poses(self):
        return [Vector3.from_vector3d(data.pose.position) for data in self.behaviour_data]

    def orientations(self):
        return [Quaternion.from_quaternion(data.pose.orientation) for data in self.behaviour_data]


class LearningRobotManager(object):
    """
    Class to manage a single robot
    """

    def __init__(
            self,
            program_arguments,
            robot,
            start_position: Vector3,
            inserted_time,
    ):
        """
        :param program_arguments:
        :param robot: RevolveBot
        :param inserted_time:
        :type inserted_time: Time
        :return:
        """

        self.robot = robot
        self.inserted_time = inserted_time
        self.start_position = start_position
        self.program_arguments = program_arguments
        self.size = robot.size()
        self._positions = []
        self._times = []
        self._time = 0.0
        self._dist = 0.0
        self._contacts = []
        self.dead = False
        self.last_fitness = None
        self.evaluations = []

        self.best_evaluation = None

    @property
    def name(self):
        return str(self.robot.id)

    def learning_step_done(self, report: LearningRobotStates):
        """
        :param report: report message sent from the simulator (routed from the WorldManager)
        :type report: LearningRobotStates
        """
        self.dead = self.dead or report.dead
        self.last_fitness = report.fitness
        evaluation = Evaluation(
            eval_n=report.eval,
            fitness=report.fitness,
            behaviour=report.behaviour,
        )
        self._positions = evaluation.poses()
        self._orientations = evaluation.orientations()
        if len(self._positions) > 0:
            self._dist = (self._positions[-1] - self._positions[0]).magnitude()
        else:
            self._dist = 0.0
        self._times = evaluation.times()
        self._time = self._times[-1] - self._times[0]

        self.evaluations.append(evaluation)

        if self.best_evaluation is None or report.fitness > self.best_evaluation.fitness:
            self.best_evaluation = evaluation
