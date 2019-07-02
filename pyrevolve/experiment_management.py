import os
import shutil
import numpy as np
from pyrevolve.custom_logging.logger import logger

class ExperimentManagement:

    # ids of robots in the name of all types of files are always phenotype ids, and the standard for id is 'robot_ID'

    def __init__(self, settings):
        self.settings = settings
        self.dirpath = 'experiments/'+self.settings.experiment_name

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

    def export_genotype(self, individual):
        if self.settings.recovery_enabled:
            individual.genotype.export_genotype(self.dirpath
                                                +'/data_fullevolution/genotypes/genotype_'+str(individual.phenotype.id)+'.txt')

    def export_phenotype(self, individual):
        if self.settings.export_phenotype:
            individual.phenotype.save_file(self.dirpath
                                           +'/data_fullevolution/phenotypes/phenotype_'+str(individual.phenotype.id)+'.yaml')

    def export_fitnesses(self, individuals):
        for individual in individuals:
            self.export_fitness(individual)

    def export_fitness(self, individual):
        f = open(f'{self.dirpath}/data_fullevolution/fitness/fitness_{individual.phenotype.id}.txt', "w")
        f.write(str(individual.fitness))
        f.close()

    def export_behavior_measures(self, id, measures):
        with open(self.dirpath+
                  '/data_fullevolution/descriptors/behavior_desc_'+id+'.txt', "w") as f:
            for key,val in measures.items():
                f.write("{} {}\n".format(key, val))


    def export_phenotype_images(self, dirpath, individual):
        individual.phenotype.render_body(self.dirpath+'/'+dirpath+'/body_'+str(individual.phenotype.id)+'.png')
        individual.phenotype.render_brain(self.dirpath +'/'+dirpath+'/brain_' + str(individual.phenotype.id))

    def export_failed_eval_robot(self,individual):
        individual.genotype.export_genotype(f'{self.dirpath}/data_fullevolution/failed_eval_robots/genotype_{str(individual.phenotype.id)}.txt')
        individual.phenotype.save_file(f'{self.dirpath}/data_fullevolution/failed_eval_robots/phenotype_{str(individual.phenotype.id)}.yaml')
        individual.phenotype.save_file(f'{self.dirpath}/data_fullevolution/failed_eval_robots/phenotype_{str(individual.phenotype.id)}.sdf', conf_type='sdf')


    def export_snapshots(self, individuals, gen_num):
        if self.settings.recovery_enabled:
            path = '/selectedpop_'+str(gen_num)
            if os.path.exists(self.dirpath+path):
                shutil.rmtree(self.dirpath+path)
            os.mkdir(self.dirpath+path)
            for ind in individuals:
                self.export_phenotype_images('selectedpop_'+str(gen_num), ind)
            logger.info('Exported snapshot '+str(gen_num)+' with ' + str(len(individuals))+' individuals')

    def experiment_is_new(self):
        if not os.path.exists(self.dirpath):
            return True
        path, dirs, files = next(os.walk(self.dirpath +'/data_fullevolution/fitness'))
        if len(files) == 0:
            return True
        else:
            return False

    def read_recovery_state(self, population_size, offspring_size):
        snapshots = []
        for r, d, f in os.walk(self.dirpath):
            for dir in d:
                if 'selectedpop' in dir:
                    snapshots.append(int(dir.split('_')[1]))
        if len(snapshots) > 0:
            last_snapshot = np.sort(snapshots)[-1]
            # number of robots expected until the snapshot
            n_robots = population_size + last_snapshot * offspring_size
        else:
            last_snapshot = -1
            n_robots = 0

        robot_ids = []
        for r, d, f in os.walk(self.dirpath +'/data_fullevolution/fitness'):
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
