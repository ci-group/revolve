import sqlalchemy
from sqlalchemy import Column, ForeignKey, ForeignKeyConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Robot(Base):
    __tablename__ = 'robot'
    id = Column(sqlalchemy.Integer, primary_key=True)
    name = Column(sqlalchemy.String, unique=True, nullable=False)


class RobotEvaluation(Base):
    __tablename__ = 'robot_evaluation'

    # Robot being evaluated
    robot_id = Column(sqlalchemy.Integer, ForeignKey(Robot.id), primary_key=True, nullable=False)
    # number of the evaluation
    n = Column(sqlalchemy.Integer, primary_key=True, nullable=False)

    # Fitness of an evaluation
    fitness = Column(sqlalchemy.Float)
    # data field to put whatever you want, made for Lamarckian evolution
    controller = Column(sqlalchemy.String)
    # name of the task accomplished
    task = Column(sqlalchemy.String)

    # Relationships
    robot = relationship(Robot)


class RobotState(Base):
    __tablename__ = 'robot_state'

    # Key
    time_sec = Column(sqlalchemy.Integer, primary_key=True)
    time_nsec = Column(sqlalchemy.Integer, primary_key=True)
    evaluation_n = Column(sqlalchemy.Integer, primary_key=True)  # ForeignKey to RobotEvaluation.n constraint: look at __tableargs__
    evaluation_robot_id = Column(sqlalchemy.Integer, ForeignKey(Robot.id), primary_key=True) # ForeignKey to RobotEvaluation.robot_id constraint: look at __tableargs__

    pos_x = Column(sqlalchemy.Float, nullable=False)
    pos_y = Column(sqlalchemy.Float, nullable=False)
    pos_z = Column(sqlalchemy.Float, nullable=False)
    rot_quaternion_x = Column(sqlalchemy.Float, nullable=False)
    rot_quaternion_y = Column(sqlalchemy.Float, nullable=False)
    rot_quaternion_z = Column(sqlalchemy.Float, nullable=False)
    rot_quaternion_w = Column(sqlalchemy.Float, nullable=False)
    orientation_forward = Column(sqlalchemy.Float, nullable=False)
    orientation_left    = Column(sqlalchemy.Float, nullable=False)
    orientation_back    = Column(sqlalchemy.Float, nullable=False)
    orientation_right   = Column(sqlalchemy.Float, nullable=False)
    # composite foreign keys are defined like this:
    __tableargs__ = (ForeignKeyConstraint((evaluation_n, evaluation_robot_id),
                                          [RobotEvaluation.n, RobotEvaluation.robot_id]),
                     {})

    # Relationships
    evaluation = relationship(RobotEvaluation)
    robot = relationship(Robot, viewonly=True)


def create_db(engine):
    # Create all tables in the engine. This is equivalent to "Create Table"
    # statements in raw SQL
    Base.metadata.create_all(engine)
