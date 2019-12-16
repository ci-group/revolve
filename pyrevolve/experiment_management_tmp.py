import os
import shutil
import numpy as np
from pyrevolve.custom_logging.logger import logger
import sys


class ExperimentManagement:
    # ids of robots in the name of all types of files are always phenotype ids, and the standard for id is 'robot_ID'

    def __init__(self, settings, environments):
        self.settings = settings
        self.environments = environments
        manager_folder = os.path.dirname(self.settings.manager)
        self._experiment_folder = os.path.join(manager_folder, 'data', self.settings.experiment_name, self.settings.run)
        self._data_folder = os.path.join(self._experiment_folder, 'data_fullevolution')

    def create_exp_folders(self):
        if os.path.exists(self.experiment_folder):
            shutil.rmtree(self.experiment_folder)
        os.makedirs(self.experiment_folder)
        os.mkdir(self.data_folder)
        os.mkdir(os.path.join(self.data_folder, 'genotypes'))
        os.mkdir(os.path.join(self.data_folder, 'failed_eval_robots'))

        for environment in self.environments:
            os.mkdir(os.path.join(self.experiment_folder, f'selectedpop_{environment}'))
            os.mkdir(os.path.join(self.data_folder, environment))
            os.mkdir(os.path.join(self.data_folder, environment, 'individuals'))
            os.mkdir(os.path.join(self.data_folder, environment, 'phenotypes'))
            os.mkdir(os.path.join(self.data_folder, environment, 'descriptors'))
            os.mkdir(os.path.join(self.data_folder, environment, 'fitness'))
            os.mkdir(os.path.join(self.data_folder, environment, 'phenotype_images'))

    @property
    def experiment_folder(self):
        return self._experiment_folder

    @property
    def data_folder(self):
        return self._data_folder

    def export_genotype(self, individual):
        if self.settings.recovery_enabled:
            individual.export_genotype(self.data_folder)

    def export_phenotype(self, individual, environment):
        if self.settings.export_phenotype:
            individual.export_phenotype(os.path.join(self.data_folder, environment))

    def export_fitnesses(self, individuals, environment):
        folder = self.data_folder
        for individual in individuals:
            individual.export_fitness(os.path.join(folder, environment))

    def export_fitness(self, individual, environment):
        folder = os.path.join(self.data_folder, environment, 'fitness')
        individual.export_fitness(folder)

    def export_individual(self, individual, environment):
        folder = os.path.join(self.data_folder, environment)
        individual.export_individual(folder)

    def export_behavior_measures(self, _id, measures, environment):
        filename = os.path.join(self.data_folder, environment, 'descriptors', f'behavior_desc_{_id}.txt')
        with open(filename, "w") as f:
            if measures is None:
                f.write(str(None))
            else:
                for key, val in measures.items():
                    f.write(f"{key} {val}\n")

    def export_phenotype_images(self, dirpath, individual):
        individual.phenotype.render_body(os.path.join(self.experiment_folder, dirpath, f'body_{individual.phenotype.id}.png'))
        individual.phenotype.render_brain(os.path.join(self.experiment_folder, dirpath, f'brain_{individual.phenotype.id}.png'))

    def export_failed_eval_robot(self, individual):
        individual.genotype.export_genotype(os.path.join(self.data_folder, 'failed_eval_robots', f'genotype_{individual.phenotype.id}.txt'))
        individual.phenotype.save_file(os.path.join(self.data_folder, 'failed_eval_robots', f'phenotype_{individual.phenotype.id}.yaml'))
        individual.phenotype.save_file(os.path.join(self.data_folder, 'failed_eval_robots', f'phenotype_{individual.phenotype.id}.sdf'), conf_type='sdf')

    def export_snapshots(self, individuals, gen_num):
        if self.settings.recovery_enabled:
            for environment in self.environments:
                path = os.path.join(self.experiment_folder, f'selectedpop{environment}', f'selectedpop_{gen_num}')
                if os.path.exists(path):
                    shutil.rmtree(path)
                os.mkdir(path)

                for ind in individuals:
                    self.export_phenotype_images(os.path.join(f'selectedpop_{environment}', f'selectedpop_{str(gen_num)}', ind[environment]))
                logger.info(f'Exported snapshot {str(gen_num)} with {str(len(individuals))} individuals')

    def experiment_is_new(self):
        if not os.path.exists(self.experiment_folder):
            return True
        # if any robot in any environment has been finished
        for environment in self.environments:
            path, dirs, files = next(os.walk(os.path.join(self.data_folder, environment, 'individuals')))
            if len(files) > 0:
                return False
        return True

    def read_recovery_state(self, population_size, offspring_size):
        snapshots = []

        # checks existent robots using the last environment of the dict as reference
        last_env = list(self.environments.keys())[-1]
        environment_snapshot_path = os.path.join(self.experiment_folder, f'selectedpop_{last_env}')
        for r, d, f in os.walk(environment_snapshot_path):
            for dir in d:
                if 'selectedpop' in dir:
                    exported_files = len([name for name in os.listdir(os.path.join(environment_snapshot_path, dir))
                                          if os.path.isfile(os.path.join(environment_snapshot_path, dir, name))])

                    # snapshot is complete if all body/brain files exist
                    if exported_files == (population_size * 2):
                        snapshots.append(int(dir.split('_')[1]))

        if len(snapshots) > 0:
            # the latest complete snapshot
            last_snapshot = np.sort(snapshots)[-1]
            # number of robots expected until the snapshot
            n_robots = population_size + last_snapshot * offspring_size
        else:
            last_snapshot = -1
            n_robots = 0

        # if a robot is developed in any of the environments, then it exists
        robot_ids = []
        for environment in self.environments:
            for r, d, f in os.walk(os.path.join(self.data_folder, environment, 'individuals')):
                for file in f:
                    robot_ids.append(int(file.split('.')[0].split('_')[-1]))
        last_id = np.sort(robot_ids)[-1]

        # if there are more robots to recover than the number expected in this snapshot
        if last_id > n_robots:
            # then recover also this partial offspring
            has_offspring = True
        else:
            has_offspring = False

        return last_snapshot, has_offspring, last_id+1
