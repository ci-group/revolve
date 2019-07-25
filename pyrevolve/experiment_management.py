import os
import shutil
import numpy as np
from pyrevolve.custom_logging.logger import logger
import sys


class ExperimentManagement:
    # ids of robots in the name of all types of files are always phenotype ids, and the standard for id is 'robot_ID'

    def __init__(self, settings):
        self.settings = settings
        self.dirpath = os.path.join('experiments', self.settings.experiment_name)

    def create_exp_folders(self):
        if os.path.exists(self.dirpath):
            shutil.rmtree(self.dirpath)
        os.mkdir(self.dirpath)
        os.mkdir(self.dirpath+'/data_fullevolution')
        os.mkdir(self.dirpath+'/data_fullevolution/genotypes')
        os.mkdir(self.dirpath+'/data_fullevolution/phenotypes')
        os.mkdir(self.dirpath+'/data_fullevolution/descriptors')
        os.mkdir(self.dirpath+'/data_fullevolution/fitness')
        os.mkdir(self.dirpath+'/data_fullevolution/phenotype_images')
        os.mkdir(self.dirpath+'/data_fullevolution/failed_eval_robots')

    def _experiment_folder(self):
        return self.dirpath

    def _data_folder(self):
        return os.path.join(self.dirpath, 'data_fullevolution')

    def export_genotype(self, individual):
        if self.settings.recovery_enabled:
            individual.export_genotype(self._data_folder())

    def export_phenotype(self, individual):
        if self.settings.export_phenotype:
            individual.export_phenotype(self._data_folder())

    def export_fitnesses(self, individuals):
        folder = self._data_folder()
        for individual in individuals:
            individual.export_fitness(folder)

    def export_fitness(self, individual):
        folder = self._data_folder()
        individual.export_fitness(folder)

    def export_behavior_measures(self, _id, measures):
        filename = os.path.join(self._data_folder(), 'descriptors', f'behavior_desc_{_id}.txt')
        with open(filename, "w") as f:
            for key, val in measures.items():
                f.write(f"{key} {val}\n")

    def export_phenotype_images(self, dirpath, individual):
        individual.phenotype.render_body(self._experiment_folder() +'/'+dirpath+f'/body_{individual.phenotype.id}.png')
        individual.phenotype.render_brain(self._experiment_folder() +'/'+dirpath+f'/brain_{individual.phenotype.id}')

    def export_failed_eval_robot(self, individual):
        individual.genotype.export_genotype(f'{self._data_folder()}/failed_eval_robots/genotype_{str(individual.phenotype.id)}.txt')
        individual.phenotype.save_file(f'{self._data_folder()}/failed_eval_robots/phenotype_{str(individual.phenotype.id)}.yaml')
        individual.phenotype.save_file(f'{self._data_folder()}/failed_eval_robots/phenotype_{str(individual.phenotype.id)}.sdf', conf_type='sdf')

    def export_snapshots(self, individuals, gen_num):
        if self.settings.recovery_enabled:
            path = os.path.join(self._experiment_folder(), f'selectedpop_{gen_num}')
            if os.path.exists(path):
                shutil.rmtree(path)
            os.mkdir(path)
            for ind in individuals:
                self.export_phenotype_images(f'selectedpop_{str(gen_num)}', ind)
            logger.info(f'Exported snapshot {str(gen_num)} with {str(len(individuals))} individuals')

    def experiment_is_new(self):
        if not os.path.exists(self._experiment_folder()):
            return True
        path, dirs, files = next(os.walk(os.path.join(self._data_folder(), 'fitness')))
        if len(files) == 0:
            return True
        else:
            return False

    def read_recovery_state(self, population_size, offspring_size):
        snapshots = []

        for r, d, f in os.walk(self._experiment_folder()):
            for dir in d:
                if 'selectedpop' in dir:
                    exported_files = len([name for name in os.listdir(os.path.join(self._experiment_folder(), dir)) if os.path.isfile(os.path.join(self._experiment_folder(), dir, name))])
                    if exported_files == (population_size * 2): # body and brain files
                        snapshots.append(int(dir.split('_')[1]))

        if len(snapshots) > 0:
            # the latest complete snapshot
            last_snapshot = np.sort(snapshots)[-1]
            # number of robots expected until the snapshot
            n_robots = population_size + last_snapshot * offspring_size
        else:
            last_snapshot = -1
            n_robots = 0

        robot_ids = []
        for r, d, f in os.walk(os.path.join(self._data_folder(), 'fitness')):
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
