#!/usr/bin/env python3
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import List, AnyStr

from pyrevolve.custom_logging.logger import logger
from pyrevolve.tol.manage import measures
from pyrevolve.util.generation import Generation
from pyrevolve.experiment_management import ExperimentManagement

from pyrevolve.evolution.speciation.population_speciated import Speciation
from pyrevolve.evolution.population import PopulationConfig, Population
from pyrevolve.evolution.individual import Individual
from pyrevolve.evolution.individual_memento import load_individual

from pyrevolve.util.robot_identifier import RobotIdentifier


async def load_population(population: Population) -> (Population, int):

    done, has_offspring = population.config.experiment_management.read_recovery_state(population.config.population_size,
                                                                                      population.config.offspring_size)
    if done:
        logger.info('Experiment is already complete.')
        return

    await load_snapshot(population)

    generation_index = Generation.getInstance().index()
    if generation_index >= 0:
        logger.info('Recovered snapshot ' + str(generation_index) + ', pop with ' + str(
            len(population.individuals)) + ' individuals')

    return population, has_offspring


async def load_snapshot(population: Population) -> None:
    """
    Recovers all genotypes and fitnesses of robots in the lastest selected population
    :param generation_index: number of the generation snapshot to recover
    """
    data_path = population.config.experiment_management.experiment_folder
    for r, d, f in os.walk(data_path + '/selectedpop_' + str(Generation.getInstance().index())):
        for file in f:
            if 'body' in file:
                #TODO obfuscated
                robot_name = file.split('.')[0].split('_')[-2] + '_' + file.split('.')[0].split('_')[-1]
                population.individuals.append(await load_individual(population.config, robot_name))


async def load_offspring(config: PopulationConfig) -> List[Individual]:
    """
    Recovers the part of an unfinished offspring
    :param config: population configuration
    :param last_snapshot: number of robots expected until the latest snapshot
    :param population_size: Population size
    :param offspring_size: Offspring size (steady state)
    :return: the list of recovered individuals
    """
    individuals = []
    # number of robots expected until the latest snapshot
    generation_index = Generation.getInstance().index()
    if generation_index == -1:
        n_robots = 0
    else:
        n_robots = config.population_size + generation_index * config.offspring_size

    for robot_id in range(n_robots + 1, RobotIdentifier.getInstance().index()):
        individuals.append(await load_individual(config, 'robot_' + str(robot_id)))

    return individuals
