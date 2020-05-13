from __future__ import annotations

import os
import shutil
import yaml

from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.individual import Individual
from pyrevolve.tol.manage import measures

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, AnyStr, Optional
    from pyrevolve.tol.manage.measures import BehaviouralMeasurements
    from pyrevolve.evolution.speciation.genus import Genus
    from pyrevolve.evolution.speciation.species import Species
    from pyrevolve.evolution.population.population_config import PopulationConfig


class ExperimentManagement:
    EXPERIMENT_FOLDER = 'data'
    DATA_FOLDER = 'data_fullevolution'
    GENERATIONS_FOLDER = 'generations'
    # ids of robots in the name of all types of files are always phenotype ids, and the standard for id is 'robot_ID'

    def __init__(self, settings):
        self.settings = settings
        manager_folder: str = os.path.dirname(self.settings.manager)
        self._experiment_folder: str = os.path.join(manager_folder, self.EXPERIMENT_FOLDER, self.settings.experiment_name, self.settings.run)
        self._data_folder: str = os.path.join(self._experiment_folder, self.DATA_FOLDER)
        self._genotype_folder: str = os.path.join(self.data_folder, 'genotypes')
        self._phylogenetic_folder: str = os.path.join(self.data_folder, 'phylogeny')
        self._phenotype_folder: str = os.path.join(self.data_folder, 'phenotypes')
        self._phenotype_images_folder: str = os.path.join(self._phenotype_folder, 'images')
        self._fitness_file_path: str = os.path.join(self.data_folder, 'fitness.csv')
        self._fitnesses_saved = set()
        self._descriptor_folder: str = os.path.join(self.data_folder, 'descriptors')
        self._behavioural_desc_folder: str = os.path.join(self._descriptor_folder, 'behavioural')
        self._failed_robots_folder: str = os.path.join(self.data_folder, 'failed_eval_robots')
        self._generations_folder: str = os.path.join(self.experiment_folder, self.GENERATIONS_FOLDER)

    #TODO refactoring
    def create_exp_folders(self) -> None:
        """
        Creates all necessary folders for the data to be saved.
        WARNING: It deletes the current experiment folder if there is one.
        """
        if os.path.exists(self.experiment_folder):
            shutil.rmtree(self.experiment_folder)
        os.makedirs(self.experiment_folder)
        os.mkdir(self.data_folder)
        os.mkdir(self._genotype_folder)
        os.mkdir(self._phylogenetic_folder)
        os.mkdir(self._phenotype_folder)
        os.mkdir(self._descriptor_folder)
        os.mkdir(self._behavioural_desc_folder)
        os.mkdir(self._phenotype_images_folder)
        os.mkdir(self._failed_robots_folder)
        os.mkdir(self._generations_folder)

    @property
    def experiment_folder(self) -> str:
        """
        Main folder of the experiment, all experimental data should be contained inside here.

        The format of the folder is going to be:
        {manager_folder}/data/{experiment_name}/{run_number}
        """
        return self._experiment_folder

    @property
    def data_folder(self) -> str:
        """
        Folder that should contain all of the data for the all the individuals.
        It does not contain any data regarding generations.
        """
        return self._data_folder

    def generation_folder(self, gen_num: int):
        return os.path.join(self._generations_folder, f'generation_{gen_num}')

    def export_genotype(self, individual: Individual) -> None:
        """
        Export the genotype to file in the `self._genotype_folder` folder
        :param individual: individual to export
        """
        if self.settings.recovery_enabled:
            individual.export_genotype(self._genotype_folder)
            individual.export_phylogenetic_info(self._phylogenetic_folder)

    def export_phenotype(self, individual: Individual) -> None:
        """
        Export the phenotype (yaml only) to file in the `self._phenotype_folder` folder
        :param individual: individual to export
        """
        if self.settings.export_phenotype:
            individual.export_phenotype(self._phenotype_folder)

    def export_fitnesses(self, individuals: List[Individual]) -> None:
        """
        Export the fitnesses of all the individuals in the list
        :param individuals: list of individuals which fitness need exporting
        """
        for individual in individuals:
            # TODO this is very inefficient if the elements are already in the set, but at least if works
            self.export_fitness(individual)

    def export_fitness(self, individual: Individual) -> None:
        """
        Exports fitness to the fitness file. If the individual fitness is already present, the value is overridden
        :param individual: individual which fitness needs "saving"
        """
        fitness_line = f'{individual.id},{individual.fitness}\n'

        if individual.id in self._fitnesses_saved:
            # search and overwrite
            logger.warning(f'Individual({individual.id}) fitness is going to be overwritten, '
                           f'normally is not be expected')
            str_individual_id = str(individual.id)
            with open(self._fitness_file_path, 'r') as fitness_file:
                lines = fitness_file.readlines()
            with open(self._fitness_file_path, 'w') as fitness_file:
                found = False
                for line in lines:
                    _file_id, _file_fitness = line.split(',')
                    if _file_id == str_individual_id:
                        logger.warning(f'Individual({individual.id}) fitness overwritten, '
                                       f'the old value was {_file_fitness}')
                        fitness_file.write(fitness_line)
                        found = True
                    else:
                        fitness_file.write(line)

                if not found:
                    logger.error(f"fitness of individual_{str_individual_id} should have been in fitness.csv file but "
                                 f"was not found, appending at the end")
                    self._fitnesses_saved.remove(individual.id)
                    self.export_fitness(individual)
        else:
            # append at the end
            with open(self._fitness_file_path, 'a') as fitness_file:
                fitness_file.write(fitness_line)
                self._fitnesses_saved.add(individual.id)

    def export_behavior_measures(self, _id: int, measures: BehaviouralMeasurements) -> None:
        """
        Exports behavioural measurements of an individual in the correct folder
        :param _id: id of the individual
        :param measures: Behavioral measurements of the individual
        """
        filename = os.path.join(self._behavioural_desc_folder, f'behavior_desc_{_id}.txt')
        with open(filename, 'w') as f:
            if measures is None:
                f.write(str(None))
            else:
                for key, val in measures.items():
                    f.write(f'{key} {val}\n')

    def export_phenotype_images(self, individual: Individual, dirpath: Optional[str] = None, rename_if_present=False) -> None:
        dirpath = dirpath if dirpath is not None \
            else self._phenotype_images_folder
        try:
            # -- Body image --
            body_filename_part = os.path.join(dirpath, f'body_{individual.phenotype.id}')
            if rename_if_present and os.path.exists(f'{body_filename_part}.png'):
                counter = 1
                while os.path.exists(f'{body_filename_part}_{counter}.png'):
                    counter += 1
                os.symlink(f'body_{individual.phenotype.id}.png',
                           f'{body_filename_part}_{counter}.png',
                           target_is_directory=False)
            else:
                # Write file
                individual.phenotype.render_body(f'{body_filename_part}.png')

            # -- Brain image --
            brain_filename_part = os.path.join(dirpath, f'brain_{individual.phenotype.id}')
            if rename_if_present and os.path.exists(f'{brain_filename_part}.png'):
                counter = 1
                while os.path.exists(f'{brain_filename_part}_{counter}.png'):
                    counter += 1
                os.symlink(f'brain_{individual.phenotype.id}.png',
                           f'{brain_filename_part}_{counter}.png',
                           target_is_directory=False)
            else:
                # Write file
                individual.phenotype.render_brain(os.path.join(dirpath, f'{brain_filename_part}.png'))
        except Exception as e:
            logger.warning(f'Error rendering phenotype images: {e}')

    def export_failed_eval_robot(self, individual: Individual) -> None:
        """
        Exports genotype and phenotype of a failed individual in the "failed individuals" folder
        :param individual: Individual that failed
        """
        individual.genotype.export_genotype(os.path.join(self._failed_robots_folder, f'genotype_{individual.phenotype.id}.txt'))
        individual.phenotype.save_file(os.path.join(self._failed_robots_folder, f'phenotype_{individual.phenotype.id}.yaml'))
        individual.phenotype.save_file(os.path.join(self._failed_robots_folder, f'phenotype_{individual.phenotype.id}.sdf'), conf_type='sdf')

    #TODO refactoring
    def export_snapshots(self, individuals: List[Individual], gen_num: int) -> None:
        if self.settings.recovery_enabled:
            path = os.path.join(self._generations_folder, f'generation_{gen_num}')
            if os.path.exists(path):
                shutil.rmtree(path)
            os.mkdir(path)
            for ind in individuals:
                self.export_phenotype_images(ind, os.path.join(self.experiment_folder, f'selectedpop_{gen_num}'))
            logger.info(f'Exported snapshot {gen_num} with {len(individuals)} individuals')

    def export_snapshots_species(self, genus: Genus, gen_num: int) -> None:
        if self.settings.recovery_enabled:
            path = os.path.join(self._generations_folder, f'generation_{gen_num}')
            if os.path.exists(path):
                shutil.rmtree(path)
            os.mkdir(path)
            for species in genus.species_collection:
                species_on_disk = os.path.join(path, f'species_{species.id}.yaml')
                species_folder = os.path.join(path, f'species_{species.id}')
                os.mkdir(species_folder)
                species.serialize(species_on_disk)
                for individual, _ in species.iter_individuals():
                    self.export_phenotype_images(individual, species_folder, rename_if_present=True)

    def experiment_is_new(self) -> bool:
        """
        Tests if the experiment is new or there is already some data that can be recovered
        :return: False if there is already some data that could be recovered
        """
        if not os.path.exists(self.experiment_folder):
            return True
        fitness_file = self._fitness_file_path
        if not os.path.isfile(fitness_file):
            return True
        if os.stat(fitness_file).st_size == 0:
            return True

        return False

    def read_recovery_state(self, population_size: int, offspring_size: int, species=False) -> (int, bool, int):
        """
        Read the saved data to determine how many generations have been completed and
        if the last generation has partially started evaluating.

        It also resets and reloads the `self._fitnesses_saved` set

        It assumes that, if the N generation is successfully completed,
        also the 0..N-1 generation are successfully completed.

        :param population_size: how many individuals should each generation have
        :param offspring_size: how many offspring to expect for each generation
        :param species: if the data we are about to read is from a speciated population
        :return: (last complete generation), (the next generation already has some data), (next robot id)
        """

        # the latest complete snapshot
        last_complete_generation = -1
        last_species_id = -1

        if not species:
            for folder in os.scandir(self.experiment_folder):
                if folder.is_dir() and folder.name.startswith('selectedpop_'):
                    # Normal population
                    n_exported_files = 0
                    for file in os.scandir(folder.path):
                        if file.is_file():
                            n_exported_files += 1

                    if n_exported_files == population_size:
                        generation_n = folder.name.split('_')[1]
                        if generation_n > last_complete_generation:
                            last_complete_generation = generation_n
        else:
            # Species!
            for folder in os.scandir(self._generations_folder):
                if folder.is_dir() and folder.name.startswith('generation_'):
                    n_exported_genomes = 0
                    for species_on_disk in os.scandir(folder.path):
                        species_on_disk: os.DirEntry
                        if not species_on_disk.is_file():
                            continue
                        with open(species_on_disk.path) as file:
                            species = yaml.load(file, Loader=yaml.SafeLoader)
                            n_exported_genomes += len(species['individuals_ids'])
                            species_id = species['id']

                        if species_id > last_species_id:
                            last_species_id = species_id

                    if n_exported_genomes == population_size:
                        generation_n = int(folder.name[len('generation_'):])
                        if generation_n > last_complete_generation:
                            last_complete_generation = generation_n

        if last_complete_generation > 0:
            # number of robots expected until the snapshot
            expected_n_robots: int = population_size + last_complete_generation * offspring_size
        else:
            expected_n_robots = 0

        # reset the fitnesses read
        self._fitnesses_saved = set()

        last_id_with_fitness = -1
        with open(self._fitness_file_path, 'r') as fitness_file:
            for line in fitness_file:
                individual_id, _fitness = line.split(',')
                individual_id = int(individual_id)
                self._fitnesses_saved.add(individual_id)
                if individual_id > last_id_with_fitness:
                    last_id_with_fitness = individual_id

        # if there are more robots to recover than the number expected in this snapshot
        if last_id_with_fitness > expected_n_robots:
            # then recover also this partial offspring
            has_offspring = True
        else:
            has_offspring = False

        # last complete generation, the next generation already has some data, next robot id
        #TODO return also last species ID
        return last_complete_generation, has_offspring, last_id_with_fitness+1, last_species_id+1,

    def load_individual(self,
                        _id: AnyStr,
                        config: PopulationConfig,
                        fitness: Optional[str] = None) -> Individual:
        """
        Loads an individual from disk
        :param _id: id of the robot to load
        :param config: population config, needed to know which genome to load
        :param fitness: optionally pass the fitness already in, to speed up the loading process.
        Pass it the fitness as a 'None' instead of None or it will read the file anyway.
        :return: the Individual loaded from the file system
        """

        genotype = config.genotype_constructor(config.genotype_conf, _id)
        genotype.load_genotype(
            os.path.join(self._genotype_folder, f'genotype_{_id}.txt'))

        individual = Individual(genotype)
        individual.develop()
        individual.phenotype.update_substrate()
        individual.phenotype.measure_phenotype()

        # load fitness
        if fitness is None:
            with open(self._fitness_file_path, 'r') as fitness_file:
                for line in fitness_file:
                    line_id, line_fitness = line.split(',')
                    if line_id == _id:
                        fitness = None if line_fitness.startswith('None') else float(line_fitness)
                        break
                else:
                    fitness = None

        individual.fitness = None if fitness is None else float(fitness)

        with open(os.path.join(self._behavioural_desc_folder, f'behavior_desc_{_id}.txt')) as f:
            lines = f.readlines()
            if lines[0] == 'None':
                individual.phenotype._behavioural_measurements = None
            else:
                individual.phenotype._behavioural_measurements = measures.BehaviouralMeasurements()
                for line in lines:
                    line_split = line.split(' ')
                    line_0 = line_split[0]
                    line_1 = line_split[1]
                    if line_0 == 'velocity':
                        individual.phenotype._behavioural_measurements.velocity = \
                            float(line_1) if line_1 != 'None\n' else None
                    # if line_0 == 'displacement':
                    #     individual.phenotype._behavioural_measurements.displacement = \
                    #         float(line_1) if line_1 != 'None\n' else None
                    elif line_0 == 'displacement_velocity':
                        individual.phenotype._behavioural_measurements.displacement_velocity = \
                            float(line_1) if line_1 != 'None\n' else None
                    elif line_0 == 'displacement_velocity_hill':
                        individual.phenotype._behavioural_measurements.displacement_velocity_hill = \
                            float(line_1) if line_1 != 'None\n' else None
                    elif line_0 == 'head_balance':
                        individual.phenotype._behavioural_measurements.head_balance = \
                            float(line_1) if line_1 != 'None\n' else None
                    elif line_0 == 'contacts':
                        individual.phenotype._behavioural_measurements.contacts = \
                            float(line_1) if line_1 != 'None\n' else None

        return individual
