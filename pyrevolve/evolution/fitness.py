import random as py_random
from pyrevolve.tol.manage import measures

def stupid(robot_manager):
    return 1.0

def random(robot_manager):
    return py_random.random()

def displacement_velocity(robot_manager):
    return measures.displacement_velocity(robot_manager)

def online_old_revolve(robot_manager):
    """
    Fitness is proportional to both the displacement and absolute
    velocity of the center of mass of the robot, in the formula:

    (1 - d l) * (a dS + b S + c l)

    Where dS is the displacement over a direct line between the
    start and end points of the robot, S is the distance that
    the robot has moved and l is the robot size.

    Since we use an active speed window, we use this formula
    in context of velocities instead. The parameters a, b and c
    are modifyable through config.
    :return:
    """
    age = robot_manager.age()
    if age < (0.25 * robot_manager.conf.evaluation_time) \
       or age < robot_manager.conf.warmup_time:
        # We want at least some data
        return 0.0

    v_fac = robot_manager.conf.fitness_velocity_factor
    d_fac = robot_manager.conf.fitness_displacement_factor
    s_fac = robot_manager.conf.fitness_size_factor
    d = 1.0 - (robot_manager.conf.fitness_size_discount * robot_manager.size)
    v = d * (d_fac * measures.displacement_velocity(robot_manager)
             + v_fac * measures.velocity(robot_manager)
             + s_fac * robot_manager.size)
    return v if v <= robot_manager.conf.fitness_limit else 0.0

def displacement_velocity_hill(robot_manager):
    _displacement_velocity_hill = displacement_velocity_hill(robot_manager)
    if _displacement_velocity_hill < 0:
        _displacement_velocity_hill /= 10
    elif _displacement_velocity_hill == 0:
        _displacement_velocity_hill = -0.1
    # temp elif
    elif _displacement_velocity_hill > 0:
        _displacement_velocity_hill *= _displacement_velocity_hill

    return _displacement_velocity_hill

def floor_is_lava(robot_manager):

    _displacement_velocity_hill = displacement_velocity_hill(robot_manager)
    _sum_of_contacts = sum_of_contacts(robot_manager)
    if _displacement_velocity_hill >= 0:
        fitness = _displacement_velocity_hill *_(1/_sum_of_contacts)
    else:
        fitness = _displacement_velocity_hill /_(1/_sum_of_contacts)

    return fitness