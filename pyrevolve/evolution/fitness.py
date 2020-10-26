import random as py_random
from pyrevolve.tol.manage import measures
import shutil


def stupid(_robot_manager, robot):
    return 1.0


def random(_robot_manager, robot):
    return py_random.random()


def displacement(behavioural_measurements, robot):
    if behavioural_measurements is not None:
        displacement_vec = behavioural_measurements['displacement'][0]
        displacement_vec.z = 0
        return displacement_vec.magnitude()
    else:
        return None

def displacement_velocity(behavioural_measurements, robot):
    if behavioural_measurements is not None:
        return behavioural_measurements['displacement_velocity']
    else:
        return None

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
    :return: fitness value
    """
    # these parameters used to be command line parameters
    warmup_time = 0.0
    v_fac = 1.0  # fitness_velocity_factor
    d_fac = 5.0  # fitness_displacement_factor
    s_fac = 0.0  # fitness_size_factor
    fitness_size_discount = 0.0
    fitness_limit = 1.0

    age = robot_manager.age()
    if age < (0.25 * robot_manager.conf.evaluation_time) \
            or age < warmup_time:
        # We want at least some data
        return 0.0

    d = 1.0 - (fitness_size_discount * robot_manager.size)
    v = d * (d_fac * measures.displacement_velocity(robot_manager)
             + v_fac * measures.velocity(robot_manager)
             + s_fac * robot_manager.size)
    return v if v <= fitness_limit else 0.0


def size_penalty(robot):
    _size_penalty = 1 / robot.phenotype._morphological_measurements.measurements_to_dict()['absolute_size']

    return _size_penalty


def novelty(behavioural_measurements, robot):
    return robot.novelty


def fast_novel_limbic(behavioural_measurements, robot):

    if behavioural_measurements is not None:
        displacement_velocity_hill = behavioural_measurements['displacement_velocity_hill']
        novelty = robot.novelty
        limbic_penalty = max(0.1, 1 - robot.phenotype._morphological_measurements.measurements_to_dict()['length_of_limbs'])

        print(robot.phenotype._id, displacement_velocity_hill , novelty , limbic_penalty)
        
        if displacement_velocity_hill >= 0:
            fitness = displacement_velocity_hill * novelty * limbic_penalty
        else:
            fitness = displacement_velocity_hill / novelty / limbic_penalty

        return fitness

    else:
        return None

def fast_novel(behavioural_measurements, robot):

    if behavioural_measurements is not None:
        displacement_velocity_hill = behavioural_measurements['displacement_velocity_hill']
        novelty = max(0.1, robot.novelty)

        print(robot.phenotype._id, displacement_velocity_hill , novelty)

        if displacement_velocity_hill >= 0:
            fitness = displacement_velocity_hill * noveltyy
        else:
            fitness = displacement_velocity_hill / novelty

        return fitness

    else:
        return None


def displacement_velocity_hill(behavioural_measurements, robot):

    if behavioural_measurements is not None:
        fitness = behavioural_measurements['displacement_velocity_hill']

        if fitness == 0 or robot.phenotype._morphological_measurements.measurements_to_dict()['hinge_count'] == 0:
            fitness = -0.1

        elif fitness < 0:
            fitness /= 10

        return fitness
    else:
        return None


def gecko(robot):

    points = 0
    # TODO: add sensors zero and joints position/coverage is maybe redundant
    if robot.phenotype._morphological_measurements.measurements_to_dict()['absolute_size'] == 13:
        points +=1
    if robot.phenotype._morphological_measurements.measurements_to_dict()['proportion'] == 1:
        points +=1
    if robot.phenotype._morphological_measurements.measurements_to_dict()['extremities'] == 4:
        points +=1

    if robot.phenotype._morphological_measurements.measurements_to_dict()['symmetry'] == 1:
        points +=1
    # if robot.phenotype._morphological_measurements.measurements_to_dict()['coverage'] == 0.52:
    #     points +=1

    # if robot.phenotype._morphological_measurements.measurements_to_dict()['active_hinges_count'] == 6:
    #     points +=1
    # if robot.phenotype._morphological_measurements.measurements_to_dict()['brick_count'] == 6:
    #     points +=1
    # if robot.phenotype._morphological_measurements.measurements_to_dict()['extensiveness'] == 7:
    #     points +=1

    test = 'gecko_1'
    if points == 4:#8:
        path_from ='experiments/karines_experiments/data/'+test+'/data_fullevolution/plane/phenotype_images/body_'\
              +str(robot.phenotype._id)+'.png'
        path_to ='experiments/karines_experiments/data/'+test+'/body_'\
              +str(robot.phenotype._id)+'.png'
        shutil.copy(path_from, path_to)

    return points * robot.novelty

    
def floor_is_lava(behavioural_measurements, robot, cost=False):
    _displacement_velocity_hill = displacement_velocity_hill(behavioural_measurements, robot, cost)
    _contacts = measures.contacts(robot_manager, robot)

    _contacts = max(_contacts, 0.0001)
    if _displacement_velocity_hill >= 0:
        fitness = _displacement_velocity_hill / _contacts
    else:
        fitness = _displacement_velocity_hill * _contacts

    return fitness
