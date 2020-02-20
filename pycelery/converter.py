from pyrevolve.evolution.individual import Individual
from pyrevolve.tol.manage import measures
from pyrevolve.SDF.math import Vector3

class NameSpace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def pop_to_dic(populationconfig):
    """
    A converter function which converts the populationconfig namespace to a dictionary.
    Currently not in use.

    :param populationconfig: The populationconfig
    :return Dic: A dictionary containing all the populationconfigurations.
    """

    Dic={}
    Dic["population_size"] = populationconfig.population_size
    Dic["genotype_constructor"] = populationconfig.genotype_constructor
    Dic["genotype_conf"] = populationconfig.genotype_conf
    Dic["fitness_function"] = populationconfig.fitness_function
    Dic["mutation_operator"] = populationconfig.mutation_operator
    Dic["mutation_conf"] = populationconfig.mutation_conf
    Dic["crossover_operator"] = populationconfig.crossover_operator
    Dic["crossover_conf"] = populationconfig.crossover_conf
    Dic["selection"] = populationconfig.selection
    Dic["parent_selection"] = populationconfig.parent_selection
    Dic["population_management"] = populationconfig.population_management
    Dic["population_management_selector"] = populationconfig.population_management_selector
    Dic["evaluation_time"] = populationconfig.evaluation_time
    Dic["offspring_size"] = populationconfig.offspring_size
    Dic["experiment_name"] = populationconfig.experiment_name
    Dic["experiment_management"] = populationconfig.experiment_management
    Dic["next_robot_id"] = populationconfig.next_robot_id

    return Dic

def dic_to_pop(dic):
    """
    This function converts a dictionary to a PopulationConfig.

    :param dic: A dictionary of the configurations
    :return args: A populationconfig class containing the configurations.
    """

    args = NameSpace(
        population_size = Dic["population_size"],
        genotype_constructor= Dic["genotype_constructor"],
        genotype_conf = Dic["genotype_conf"],
        fitness_function = Dic["fitness_function"],
        mutation_operator = Dic["mutation_operator"],
        mutation_conf = Dic["mutation_conf"],
        crossover_operator = Dic["crossover_operator"],
        crossover_conf = Dic["crossover_conf"],
        parent_selection = Dic["parent_selection"],
        population_management = Dic["population_management"],
        population_management_selector = Dic["population_management_selector"],
        evaluation_time = Dic["evaluation_time"],
        offspring_size = Dic["offspring_size"],
        experiment_name = Dic["experiment_name"],
        experiment_management = Dic["experiment_management"],
        selection = Dic["selection"],
        next_robot_id = Dic["next_robot_id"])

    return args

def args_to_dic(settings):
    """
    A converter function to send the settings to a celery worker.

    :param settings: a settings namespace containing all the settings
    :return dic: a dictionary containing the settings
    """

    Dic = {}
    Dic['celery'] = settings.celery
    Dic["controller_update_rate"] = settings.controller_update_rate
    Dic["evaluation_time"] = settings.evaluation_time
    Dic["experiment_name"]= settings.experiment_name
    Dic["export_phenotype"]= settings.export_phenotype
    Dic["manager"]= settings.manager
    Dic["n_cores"]= settings.n_cores
    Dic["output_directory"] = settings.output_directory
    Dic["port_start"] = settings.port_start
    Dic["pose_update_frequency"] = settings.pose_update_frequency
    Dic["recovery_enabled"] = settings.recovery_enabled
    Dic["restore_directory"] = settings.restore_directory
    Dic["run"] = settings.run
    Dic["sensor_update_rate"] = settings.sensor_update_rate
    Dic["simulator_cmd"] = settings.simulator_cmd
    Dic["test_robot"] = settings.test_robot
    Dic["test_robot_collision"] = settings.test_robot_collision
    Dic["world"] = settings.world
    Dic["z_start"] = settings.z_start

    return Dic


def dic_to_args(Dic):
    """
    This function converts dictionaries back to settings namespace. A celery worker
    can use this to evaluate a settingsDir.

    :param Dic: A dictionary containing the settings
    :return args: a settings namesplace containing the settings
    """

    args = NameSpace(celery = Dic["celery"],
        controller_update_rate= Dic["controller_update_rate"],
        evaluation_time = Dic["evaluation_time"],
        experiment_name = Dic["experiment_name"],
        export_genotype = Dic["export_phenotype"],
        manager = Dic["manager"],
        n_cores = Dic["n_cores"],
        output_directory = Dic["output_directory"],
        port_start = Dic["port_start"],
        recovery_enabled = Dic["recovery_enabled"],
        pose_update_frequency = Dic["pose_update_frequency"],
        restore_directory = Dic["restore_directory"],
        run = Dic["run"],
        sensor_update_rate = Dic["sensor_update_rate"],
        simulator_cmd = Dic["simulator_cmd"],
        test_robot = Dic["test_robot"],
        test_robot_collision = Dic["test_robot_collision"],
        world = Dic["world"],
        z_start = Dic["z_start"])

    return args

def args_default():
    """
    In case default arguments are used, this function could deliver them. Converting would
    then not be necessary since a celery worker can just call this function.
    """

    args = NameSpace(celery = True,
    manager = "pycelery/manager.py",
    controller_update_rate = 8,
    evaluation_time = 30,
    experiment_name = "default_experiment",
    export_genotype = True,
    n_cores = 2,
    output_directory = "output",
    port_start = 11345,
    recovery_enabled = True,
    pose_update_frequency = 5,
    restore_directory = "restore",
    run = "1",
    sensor_update_rate = 8,
    simulator_cmd = "gazebo",
    world = "worlds/plane.world",
    z_start = 0.03,
    test_robot = None,
    test_collision_robot = None)

    return args

def measurements_to_dict(robot_manager, robot):
    """
    This function calculates the BehaviouralMeasurements of a robot and then converts
    it into a dictionary such that it can be send through celery.

    :param robot_manager: the robot_manager of the robot
    :param robot: the PHENOTYPE of the robot
    :return dic: a dictionary containing the measurements.
    """

    individual = Individual("no genotype needed", robot) # just a shell for phenotype
    measurements = measures.BehaviouralMeasurements(robot_manager, individual)

    dic = {}
    dic["velocity"] = float(measurements.velocity)
    dic["displacement_x"] = float(measurements.displacement[0].x)
    dic["displacement_y"] = float(measurements.displacement[0].y)
    dic["displacement_z"] =float( measurements.displacement[0].z)
    dic["displacement_time"] = float(measurements.displacement[1])
    dic["displacement_velocity"] = float(measurements.displacement_velocity)
    dic["displacement_velocity_hill"] = float(measurements.displacement_velocity_hill)
    dic["head_balance"] = float(measurements.head_balance)
    dic["contacts"] = float(measurements.contacts)

    return dic

def dic_to_measurements(dic):
    """
    A converter function, converting a dictionary to measurements. This is after a
    dictionary is send through celery.

    :param dic: a dictionary containing the measurements.
    :return measurements: a BehaviouralMeasurements class containing measurements.
    """
    if dic == None or dic == 'NULL':
        return None

    measurements = measures.BehaviouralMeasurements(None, None)

    measurements.velocity = dic["velocity"]
    measurements.displacement = (Vector3(dic["displacement_x"], dic["displacement_y"], dic["displacement_z"]), dic["displacement_time"])
    measurements.displacement_velocity=dic["displacement_velocity"]
    measurements.displacement_velocity_hill =dic["displacement_velocity_hill"]
    measurements.head_balance =dic["head_balance"]
    measurements.contacts =dic["contacts"]

    return measurements
