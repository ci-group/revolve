
class NameSpace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

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
