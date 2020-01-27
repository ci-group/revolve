
class NameSpace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def pop_to_dic(populationconfig):
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
    """This functions takes a NameSpace argument, and returns a dictionary.
    This dictionary is Yaml and Json serializable and therefore can be transfered
    in between tasks in celery."""

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
    """ argument: dictionary with arguments in it and its values
        return: a namespace args as used by other functions"""

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
