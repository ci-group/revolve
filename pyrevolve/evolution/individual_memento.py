#!/usr/bin/env python3
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import AnyStr

from pyrevolve.evolution.fitness import read_fitness
from pyrevolve.tol.manage.measures import create_behavioral_measures

from pyrevolve.evolution.population import PopulationConfig, Population
from pyrevolve.evolution.individual import Individual


async def load_individual(config: PopulationConfig, id: AnyStr) -> Individual:
    """
    Creates the phenotype, and fitness from the loaded genotype for the individual.
    :param config: population configuration
    :param id: id of the robot to load
    :return: the Individual loaded from the file system
    """
    data_path = config.experiment_management.data_folder
    genotype = config.genotype_constructor(config.genotype_conf, id)
    genotype.load_genotype(os.path.join(data_path, 'genotypes', f'genotype_{id}.txt'))

    individual = Individual(genotype)

    individual.develop()
    individual.phenotype.measure_phenotype()
    # TODO refactor
    individual.phenotype._behavioural_measurements = create_behavioral_measures(data_path, id)

    individual.fitness = read_fitness(data_path, id)

    return individual