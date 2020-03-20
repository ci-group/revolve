#!/usr/bin/env python3
import os

from pyrevolve.custom_logging.logger import logger
from pyrevolve.tol.manage import measures
from pyrevolve.experiment_management import ExperimentManagement

from pyrevolve.evolution.speciation.population_speciated import PopulationSpeciated
from pyrevolve.evolution.population import PopulationConfig, Population
from pyrevolve.evolution.individual import Individual

from pyrevolve.util.robot_identifier import RobotIdentifier


async def population_recovery(population_config: PopulationConfig, experiment_management: ExperimentManagement,
                              settings, population_size: int, offspring_size: int, num_generations: int,
                              do_recovery: bool, is_speciated: bool = False):

    if do_recovery:
        generation_index, has_offspring = experiment_management.read_recovery_state(population_size, offspring_size)

        if generation_index == num_generations - 1:
            logger.info('Experiment is already complete.')
            return
    else:
        has_offspring = False
        generation_index = 0

    if is_speciated:
        population = PopulationSpeciated(population_config)
    else:
        population = Population(population_config)

    if do_recovery:
        # loading a previous state of the experiment
        await load_snapshot(population, population_config, generation_index)
        if generation_index >= 0:
            logger.info('Recovered snapshot '+str(generation_index)+', pop with ' + str(len(population.individuals))+' individuals')

        # TODO has offspring is does not have to be initialized.
        if has_offspring:
            individuals = await load_offspring(population, population_config, generation_index,
                                               population_size, offspring_size)
            generation_index += 1
            logger.info('Recovered unfinished offspring '+str(generation_index))

            if generation_index == 0:
                await population.initialize(individuals)
            else:
                population = await population.next_generation(generation_index, individuals)

            experiment_management.export_snapshots(population.individuals, generation_index)
    else:
        # starting a new experiment
        experiment_management.create_exp_folders()
        await population.initialize()
        experiment_management.export_snapshots(population.individuals, generation_index)

    return population, generation_index


async def load_snapshot(population: Population, config: PopulationConfig, generation_index: int):
    """
    Recovers all genotypes and fitnesses of robots in the lastest selected population
    :param generation_index: number of the generation snapshot to recover
    """
    data_path = config.experiment_management.experiment_folder
    for r, d, f in os.walk(data_path + '/selectedpop_' + str(generation_index)):
        for file in f:
            if 'body' in file:
                #TODO obfuscated
                robot_name = file.split('.')[0].split('_')[-2] + '_' + file.split('.')[0].split('_')[-1]
                population.individuals.append(await load_individual(config, robot_name))


async def load_offspring(population: Population, config: PopulationConfig, last_snapshot,
                         population_size, offspring_size):
    """
    Recovers the part of an unfinished offspring
    :param
    :return:
    """
    individuals = []
    # number of robots expected until the latest snapshot
    if last_snapshot == -1:
        n_robots = 0
    else:
        n_robots = population_size + last_snapshot * offspring_size

    for robot_id in range(n_robots + 1, RobotIdentifier.getInstance().index()):
        individuals.append(await load_individual(config, 'robot_' + str(robot_id)))

    return individuals


async def load_individual(config: PopulationConfig, robot_name: str):
    data_path = config.experiment_management.data_folder
    genotype = config.genotype_constructor(config.genotype_conf, robot_name)
    genotype.load_genotype(os.path.join(data_path, 'genotypes', f'genotype_{robot_name}.txt'))

    individual = Individual(genotype)
    individual.develop()
    individual.phenotype.measure_phenotype()

    with open(os.path.join(data_path, 'fitness', f'fitness_{robot_name}.txt')) as f:
        data = f.readlines()[0]
        individual.fitness = None if data == 'None' else float(data)

    with open(os.path.join(data_path, 'descriptors', f'behavior_desc_{robot_name}.txt')) as f:
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
                if line_0 == 'displacement_velocity':
                    individual.phenotype._behavioural_measurements.displacement_velocity = \
                        float(line_1) if line_1 != 'None\n' else None
                if line_0 == 'displacement_velocity_hill':
                    individual.phenotype._behavioural_measurements.displacement_velocity_hill = \
                        float(line_1) if line_1 != 'None\n' else None
                if line_0 == 'head_balance':
                    individual.phenotype._behavioural_measurements.head_balance = \
                        float(line_1) if line_1 != 'None\n' else None
                if line_0 == 'contacts':
                    individual.phenotype._behavioural_measurements.contacts = \
                        float(line_1) if line_1 != 'None\n' else None

    return individual