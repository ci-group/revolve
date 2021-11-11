import os
import shutil
import numpy as np
from pyrevolve.custom_logging.logger import logger
import sys
import gzip
import pickle
import glob


class ExperimentManagement:
    # ids of robots in the name of all types of files are always phenotype ids, and the standard for id is 'robot_ID'

    def __init__(self, settings, environments):
        self.settings = settings
        self.environments = environments
        self.dirpath = os.path.join('experiments', self.settings.experiment_name)

    def create_exp_folders(self):
        if os.path.exists(self.dirpath):
            shutil.rmtree(self.dirpath)
        os.mkdir(self.dirpath)
        os.mkdir(self.dirpath+'/data_fullevolution')
        os.mkdir(self.dirpath+'/data_fullevolution/genotypes')
        os.mkdir(self.dirpath+'/data_fullevolution/genotypes/images')
        os.mkdir(self.dirpath+'/data_fullevolution/consolidated_fitness')
        os.mkdir(self.dirpath+'/data_fullevolution/failed_eval_robots')
        for environment in self.environments:
            os.mkdir(self.dirpath+'/selectedpop_'+environment)
            os.mkdir(self.dirpath+'/data_fullevolution/'+environment)
            os.mkdir(self.dirpath+'/data_fullevolution/'+environment+'/individuals')
            os.mkdir(self.dirpath+'/data_fullevolution/'+environment+'/phenotypes')
            os.mkdir(self.dirpath+'/data_fullevolution/'+environment+'/descriptors')
            os.mkdir(self.dirpath+'/data_fullevolution/'+environment+'/fitness')
            os.mkdir(self.dirpath+'/data_fullevolution/'+environment+'/novelty')
            os.mkdir(self.dirpath+'/data_fullevolution/'+environment+'/phenotype_images')

    def _experiment_folder(self):
        return self.dirpath

    def _data_folder(self):
        return os.path.join(self.dirpath, 'data_fullevolution')

    def export_genotype(self, individual):
        individual.export_genotype(self._data_folder())

    def export_parents(self, individual):
        individual.export_parents(self._data_folder())

    def stability_export(self, experiment_name, id, measures):
        filepath = 'robustness.txt'
        f = open(os.path.join(self.dirpath, 'data_fullevolution', filepath), "a")
        f.write(experiment_name+'\t'+self.settings.world+'\t'+id+'\t'+str(measures['displacement_velocity_hill'])+'\n')
        f.close()

    def export_phenotype(self, individual, environment):
        if self.settings.export_phenotype:
            individual.export_phenotype(self._data_folder()+'/'+environment)

    def export_fitness(self, individual, environment, gen_num):
        folder = os.path.join(self._data_folder(), environment, 'fitness')
        individual.export_fitness(folder, gen_num)

    def export_consolidated_fitness(self, individual, gen_num):
        folder = os.path.join(self._data_folder(), 'consolidated_fitness')
        individual.export_consolidated_fitness(folder, gen_num)

    def export_novelty(self, individual, environment, gen_num):
        folder = os.path.join(self._data_folder(), environment, 'novelty')
        individual.export_novelty(folder, gen_num)

    def export_novelty_pop(self, individual, environment, gen_num):
        folder = os.path.join(self._data_folder(), environment, 'novelty')
        individual.export_novelty_pop(folder, gen_num)

    def export_individual(self, individual, environment):
        folder = self._data_folder()+'/'+environment
        individual.export_individual(folder)

    def export_behavior_measures(self, _id, measures, environment, gen_num):
        if self.settings.resimulate != '':
            gen = str(gen_num)+'_'
        else:
            gen= ''

        filename = os.path.join(self._data_folder()+'/'+environment, 'descriptors', f'behavior_desc_{gen}{_id}.txt')
        with open(filename, "w") as f:
            if measures is None:
                f.write(str(None))
            else:
                for key, val in measures.items().items():
                    f.write(f"{key} {val}\n")

    def export_early_death(self, generation, individuals_survived):
        filename = os.path.join(self._data_folder() + '/individuals_early_survived.txt')
        f = open(filename, "a")
        f.write(generation+'\t'+individuals_survived+'\n')
        f.close()


    def export_phenotype_images(self, dirpath, individual):
        individual.phenotype.render_body(self._experiment_folder()+'/'+dirpath+f'/body_{individual.phenotype.id}.png')
        individual.phenotype.render_brain(self._experiment_folder()+'/'+dirpath+f'/brain_{individual.phenotype.id}')

    def export_failed_eval_robot(self, individual):
        individual.genotype.export_genotype(f'{self._data_folder()}/failed_eval_robots/genotype_{str(individual.phenotype.id)}.txt')
        individual.phenotype.save_file(f'{self._data_folder()}/failed_eval_robots/phenotype_{str(individual.phenotype.id)}.yaml')
        individual.phenotype.save_file(f'{self._data_folder()}/failed_eval_robots/phenotype_{str(individual.phenotype.id)}.sdf', conf_type='sdf')

    def log_species(self, gen_num, num_species, all_individuals, new_individuals):
        file = open(f'{self._data_folder()}/log_species.txt', 'a')
        file.write(f'{gen_num}\t{num_species}\t{all_individuals}\t{new_individuals}\n')
        file.close()

    def export_snapshots(self, individuals, gen_num):
        if self.settings.recovery_enabled:
            for environment in self.environments:
                path = os.path.join(self._experiment_folder()+'/selectedpop_'+environment, f'selectedpop_{gen_num}')
                if os.path.exists(path):
                    shutil.rmtree(path)
                os.mkdir(path)

                for ind in individuals:
                    self.export_phenotype_images('selectedpop_'+environment+'/'+f'selectedpop_{str(gen_num)}', ind[environment])
                logger.info(f'Exported snapshot {str(gen_num)} with {str(len(individuals))} individuals')

    def experiment_is_new(self):
        if not os.path.exists(self._experiment_folder()):
            return True
        # if any robot in any environment has been finished
        for environment in self.environments:
            path, dirs, files = next(os.walk(os.path.join(self._data_folder()+'/'+environment, 'individuals')))
            if len(files) > 0:
                return False

        return True

    def neat_experiment_is_new(self):
        if not os.path.exists(self._experiment_folder()):
            return True, None

        gens = []
        for file in glob.glob(os.path.join(self._data_folder(), 'neat_checkpoint*.pkl')):
            gens.append(int(file.split('neat_checkpoint_')[1].split('.')[0]))
        gens.sort()

        attempts = len(gens)-1
        while attempts >= 0:
            filename = self._data_folder()+'/neat_checkpoint_'+str(gens[attempts])+'.pkl'

            if os.path.isfile(filename):
                try:
                    with gzip.open(filename) as f:
                        neat, individuals = pickle.load(f)
                        checkpoint = {'neat': neat,
                                      'individuals': individuals}
                    return False, checkpoint
                except:
                    print('bad pickle for latest checkpoint')
            attempts -= 1

        return True, None

    def read_recovery_state(self, population_size, offspring_size):
        snapshots = []

        # checks existent robots using the last environment of the dict as reference
        path = self._experiment_folder()+'/selectedpop_'+list(self.environments.keys())[-1]
        for r, d, f in os.walk(path):
            for dir in d:
                if 'selectedpop' in dir:
                    exported_files = len([name for name in os.listdir(os.path.join(path,
                                                                                   dir))
                                          if os.path.isfile(os.path.join(path, dir, name)) and name.startswith("body")])

                    # snapshot is complete if all body/brain files exist
                    if exported_files == population_size:
                        snapshots.append(int(dir.split('_')[1]))

        if len(snapshots) > 0:
            # the latest complete snapshot
            last_snapshot = np.sort(snapshots)[-1]
            # number of robots expected until the snapshot
            n_robots = population_size + last_snapshot * offspring_size
        else:
            last_snapshot = -1
            n_robots = 0

        # if a robot is developed in the last environment
        robot_ids = []
        last_id = 0
        environment = list(self.environments.keys())[-1]
        for r, d, f in os.walk(os.path.join(self._data_folder()+'/'+environment, 'individuals')):
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
