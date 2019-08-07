import os
import glob
import ast
import shutil
import numpy as np
from pyrevolve.custom_logging.logger import logger
import sys


class ExperimentManagement:
    # ids of robots in the name of all types of files are always phenotype ids, and the standard for id is 'robot_ID'

    def __init__(self, settings):
        self.settings = settings
        manager_folder = os.path.dirname(self.settings.manager)
        self._experiment_folder = os.path.join(manager_folder, 'data', self.settings.experiment_name, self.settings.run)
        self._data_folder = os.path.join(self._experiment_folder, 'data_fullevolution')

    def create_exp_folders(self):
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
        os.mkdir(os.path.join(self.data_folder, 'finished_learning'))
        os.mkdir(os.path.join(self.data_folder, 'finished_generation'))

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

    def export_cma_learning_fitness(self, robot_id, generation, vector, fitness):
        """
        Append fitness of cma vectors to txt file, to recover in case of crash
        :param robot_id:
        :param vector:
        :param fitness:
        """
        f = open(f'{self.data_folder}/fitness/fitness_learning_{robot_id}_fitness.txt', 'a')
        f.write(f'{fitness}\n')
        f.close()        
        f = open(f'{self.data_folder}/fitness/fitness_learning_{robot_id}_vectors.txt', "a")
        f.write(f'{vector}\n')
        f.close()

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
        individual.phenotype.render_body(os.path.join(self.experiment_folder, dirpath, f'body_{individual.phenotype.id}.png'))
        individual.phenotype.render_brain(os.path.join(self.experiment_folder, dirpath, f'brain_{individual.phenotype.id}.png'))

    def export_failed_eval_robot(self, individual):
        individual.genotype.export_genotype(os.path.join(self.data_folder, 'failed_eval_robots', f'genotype_{individual.phenotype.id}.txt'))
        individual.phenotype.save_file(os.path.join(self.data_folder, 'failed_eval_robots', f'phenotype_{individual.phenotype.id}.yaml'))
        individual.phenotype.save_file(os.path.join(self.data_folder, 'failed_eval_robots', f'phenotype_{individual.phenotype.id}.sdf'), conf_type='sdf')

    def export_snapshots(self, individuals, gen_num):
        if self.settings.recovery_enabled:
            path = os.path.join(self.experiment_folder, f'selectedpop_{gen_num}')
            if os.path.exists(path):
                shutil.rmtree(path)
            os.mkdir(path)
            for ind in individuals:
                self.export_phenotype_images(f'selectedpop_{str(gen_num)}', ind)
            logger.info(f'Exported snapshot {str(gen_num)} with {str(len(individuals))} individuals')

    def experiment_is_new(self):
        if not os.path.exists(self.experiment_folder):
            return True
        path, dirs, files = next(os.walk(os.path.join(self.data_folder, 'fitness')))
        if len(files) == 0:
            return True
        else:
            return False

    def finished_learning(self, robot_id):
        f = open(f'{self.data_folder}/finished_learning/{robot_id}.txt', "w")
        f.write('finished')
        f.close()

    def finished_generation(self, gen_num):
        f = open(f'{self.data_folder}/finished_generation/finished_gen_{gen_num}.txt', "w")
        f.write('finished')
        f.close()

    def generation_has_finished(self, gen_num):
        return os.path.isfile(f'{self.data_folder}/finished_generation/finished_gen_{gen_num}.txt')

    def has_finished_learning(self, robot_id):
        return os.path.isfile(f'{self.data_folder}/finished_learning/{robot_id}.txt')
    
    def learning_iterations_performed(self, robot_id, generation):
        if self.cma_learning_is_recoverable(robot_id, generation):
            recovered_vals = self.recover_cma_learning_fitnesses(robot_id, generation)
            return len(recovered_vals[1])
        return 0

    def cma_learning_is_recoverable(self, robot_id, generation):
        """
        Check if file exists for learned fitness values of robot
        :param robot_id:
        :param generation:
        """
        vector_exists = os.path.isfile(f'{self.data_folder}/fitness/fitness_learning_{robot_id}_vectors.txt')
        fitness_exists = os.path.isfile(f'{self.data_folder}/fitness/fitness_learning_{robot_id}_fitness.txt')
        return vector_exists and fitness_exists

    def recover_cma_learning_fitnesses(self, robot_id, generation):
        """
        Recover vector values and corresponding fitness values
        :param robot_id:
        :param generation:
        """
        vectors = []
        fitness_vals = []

        file = open(f'{self.data_folder}/fitness/fitness_learning_{robot_id}_vectors.txt', 'r')
        list_lines = file.read().splitlines()
        for line in list_lines:
            if line:
                vector = ast.literal_eval(line)
                vectors.append(vector)
        file.close()

        file = open(f'{self.data_folder}/fitness/fitness_learning_{robot_id}_fitness.txt', 'r')
        list_lines = file.read().splitlines()
        for line in list_lines:
            if line:
                fitness = ast.literal_eval(line)
                vectors.append(vector)
                fitness_vals.append(fitness)
        file.close()

        return [vectors, fitness_vals]

    def recover_previous_gens(self, robot_id, generation):
        """
        Recover vector values and corresponding fitness values from previous gens
        :param robot_id:
        :param generation:        
        """
        vectors = []
        fitness_vals = []
        generation -= 1
        while self.cma_learning_is_recoverable(robot_id, generation):
            recovered_vals = self.recover_cma_learning_fitnesses(robot_id, generation)
            vectors += recovered_vals[0]
            fitness_vals += recovered_vals[1]
            generation -= 1
        return [vectors, fitness_vals]        

    def delete_generation_files(self, gen_num):
        """
        Delete all files from generation
        :param gen_num:
        """
        shutil.rmtree(f'{self.data_folder}/selectedpop_{gen_num}')

        robot_ids = []
        last_id = 0
        if gen_num > 0:
            for r, d, f in os.walk(f'{self.data_folder}/selectedpop_{gen_num-1}'):
                for file in f:
                    robot_ids.append(int(file.split('.')[0].split('_')[-1]))
            last_id = np.sort(robot_ids)[-1]

        os.remove(f'{self.data_folder}/finished_generation/finished_gen_{gen_num}.txt')

        for folder in ['descriptors', 'failed_eval_robots', 'finished_learning', 'fitness', 'genotypes', 'phenotype_images', 'phenotypes']:
            for r, d, f in os.walk(f'{self.data_folder}/{folder}'):
                for file in f:
                    if int(file.split('.')[0].split('_')[-1]) > last_id:
                        os.remove(f'{self.data_folder}/{folder}/{file}')

    def delete_robot_learn_files(self, robot_id):
        robot_ids = []
        for r, d, f in os.walk(f'{self.data_folder}/phenotypes'):
            for file in f:
                robot_ids.append(int(file.split('.')[0].split('_')[-1]))
        last_id = np.sort(robot_ids)[-1]     
        
        robot_ids = np.arange(robot_id, last_id+1)

        for r_id in robot_ids:
            files = glob.glob(f'{self.data_folder}/descriptors/behavior_desc_robot_{r_id}.txt')
            files += glob.glob(f'{self.data_folder}/descriptors/behavior_desc_robot_{r_id}_*.txt')
            files += glob.glob(f'{self.data_folder}/fitness/fitness_learning_robot_{r_id}_*.txt')
            files += glob.glob(f'{self.data_folder}/finished_learning/robot_{r_id}.txt')
            for file in files:
                os.remove(file)

    def read_recovery_state(self, population_size, offspring_size):
        snapshots = []

        for r, d, f in os.walk(self.experiment_folder):
            for dir in d:
                if 'selectedpop' in dir:
                    exported_files = len([name for name in os.listdir(os.path.join(self.experiment_folder, dir)) if os.path.isfile(os.path.join(self.experiment_folder, dir, name))])
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

        for r, d, f in os.walk(os.path.join(self._data_folder, 'fitness')):
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

    def write_to_fitness_file(self, robot_id, fitness):
        exists = os.path.isfile(f'{self.data_folder}/all_fitness.csv')

        f = open(f'{self.data_folder}/all_fitness.csv', 'a')

        if not exists:
            f.write(f'id, fitness\n')

        f.write(f'{robot_id}, {fitness}\n')
        f.close()  

    def write_to_speed_file(self, robot_id, measures):
        exists = os.path.isfile(f'{self.data_folder}/all_behavior.csv')

        f = open(f'{self.data_folder}/all_behavior.csv', 'a')

        if not exists:
            f.write(f'id, displacement\n')
        
        speed = None if measures is None else measures.displacement_velocity
        f.write(f'{robot_id}, {speed}\n')
        f.close()  
