import numpy as np
import shutil
import os

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from pyrevolve.evolution.individual import Individual

from typing import List

from pyrevolve.custom_logging.logger import logger

from pyrevolve.util.robot_identifier import RobotIdentifier
from pyrevolve.util.generation import Generation


class ExperimentManagement:
    # ids of robots in the name of all types of files are always phenotype ids, and the standard for id is 'robot_ID'

    def __init__(self, settings):
        self.settings = settings
        manager_folder = os.path.dirname(self.settings.manager)
        self._experiment_folder = os.path.join(manager_folder, 'data', self.settings.experiment_name, self.settings.run)
        self._data_folder = os.path.join(self._experiment_folder, 'data_fullevolution')

    def prepare_folders(self):
        if os.path.exists(self.experiment_folder):
            shutil.rmtree(self.experiment_folder)
        os.makedirs(self.experiment_folder)
        os.mkdir(self.data_folder)
        os.mkdir(os.path.join(self.data_folder, 'genotypes'))
        os.mkdir(os.path.join(self.data_folder, 'phenotypes'))
        os.mkdir(os.path.join(self.data_folder, 'descriptors'))
        os.mkdir(os.path.join(self.data_folder, 'fitness'))
        os.mkdir(os.path.join(self.data_folder, 'phenotype_images'))
        os.mkdir(os.path.join(self.data_folder, 'failed_eval_robots'))

    @property
    def experiment_folder(self):
        return self._experiment_folder

    @property
    def data_folder(self):
        return self._data_folder

    def export_genotype(self, individual):
        if self.settings.recovery_enabled:
            individual.export_genotype(self.data_folder)

    def export_phenotype(self, individual):
        if self.settings.export_phenotype:
            individual.export_phenotype(self.data_folder)

    def export_fitnesses(self, individuals):
        folder = self.data_folder
        for individual in individuals:
            individual.export_fitness(folder)

    def export_fitness(self, individual):
        folder = os.path.join(self.data_folder, 'fitness')
        individual.export_fitness(folder)

    def export_behavior_measures(self, _id, measures):
        filename = os.path.join(self.data_folder, 'descriptors', f'behavior_desc_{_id}.txt')
        with open(filename, "w") as f:
            if measures is None:
                f.write(str(None))
            else:
                for key, val in measures.items():
                    f.write(f"{key} {val}\n")

    def export_phenotype_images(self, dirpath, individual):
        try:
            individual.phenotype.render_body(os.path.join(self.experiment_folder, dirpath, f'body_{individual.phenotype.id}.png'))
            individual.phenotype.render_brain(os.path.join(self.experiment_folder, dirpath, f'brain_{individual.phenotype.id}.png'))
        except Exception as e:
            logger.warning(f'Error rendering phenotype images: {e}')

    def export_failed_eval_robot(self, individual):
        individual.genotype.export_genotype(os.path.join(self.data_folder, 'failed_eval_robots', f'genotype_{individual.phenotype.id}.txt'))
        individual.phenotype.save_file(os.path.join(self.data_folder, 'failed_eval_robots', f'phenotype_{individual.phenotype.id}.yaml'))
        individual.phenotype.save_file(os.path.join(self.data_folder, 'failed_eval_robots', f'phenotype_{individual.phenotype.id}.sdf'), conf_type='sdf')

    def export_snapshots(self, individuals: List[Individual]):

        generation_index = Generation.getInstance().index()

        if self.settings.recovery_enabled:
            path = os.path.join(self.experiment_folder, f'selectedpop_{generation_index}')
            if os.path.exists(path):
                shutil.rmtree(path)
            os.mkdir(path)
            for ind in individuals:
                self.export_phenotype_images(f'selectedpop_{str(generation_index)}', ind)
            logger.info(f'Exported snapshot {str(generation_index)} with {str(len(individuals))} individuals')

    def experiment_is_new(self):
        if not os.path.exists(self.experiment_folder):
            return True
        path, dirs, files = next(os.walk(os.path.join(self.data_folder, 'fitness')))
        if len(files) == 0:
            return True
        else:
            return False

    def read_recovery_state(self, population_size: int, offspring_size: int):
        snapshots = []

        for r, d, f in os.walk(self.experiment_folder):
            for dir in d:
                if 'selectedpop' in dir:
                    exported_files = len([name for name in os.listdir(os.path.join(self.experiment_folder, dir)) if os.path.isfile(os.path.join(self.experiment_folder, dir, name))])
                    # no brains yet so check only for body files
                    # if exported_files == (population_size * 2): # body and brain files
                    if exported_files == population_size: # body and brain files
                        snapshots.append(int(dir.split('_')[1]))

        generation = Generation.getInstance()

        if len(snapshots) > 0:
            # the latest complete snapshot
            generation.initialize(np.sort(snapshots)[-1])
            generation_index = generation.index()
            # number of robots expected until the snapshot
            n_robots = population_size + generation_index * offspring_size
        else:
            # TODO why -1? workaround of the pre-incremental step in the main for loop?
            generation.initialize(-1)
            n_robots = 0

        robot_ids = []
        for r, d, f in os.walk(os.path.join(self.data_folder, 'fitness')):
            for file in f:
                robot_ids.append(int(file.split('.')[0].split('_')[-1]))
        last_id = np.sort(robot_ids)[-1]

        # if there are more robots to recover than the number expected in this snapshot
        if last_id > n_robots:
            # then recover also this partial offspring
            has_offspring = True
        else:
            has_offspring = False

        RobotIdentifier.getInstance().initialize(last_id + 1)

        return has_offspring
