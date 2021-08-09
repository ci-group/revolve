#!/usr/bin/env python3

import math
from typing import Optional, List

import numpy as np
import matplotlib
from pyrevolve.evolution.individual import Individual
from .nsga2 import NSGA2

from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding import PlasticodingConfig

# setup matplotlib renderer correctly
gui_env = ['TKAgg', 'GTKAgg', 'Qt4Agg', 'WXAgg']
gui_env = ['tk', 'gtk', 'gtk3', 'wx', 'qt4', 'qt5', 'qt', 'osx', 'nbagg', 'notebook', 'agg', 'svg', 'pdf', 'ps',
           'inline', 'ipympl', 'widget']
for gui in gui_env:
    try:
        print(f"testing matplotlib backend {gui}")
        matplotlib.use(gui, warn=False, force=True)
        from matplotlib import pyplot as plt

        break
    except:
        continue
print(f"Using matplotlib backend: {matplotlib.get_backend()}")


class MockPopulation(Population):
    def __init__(self, conf: PopulationConfig, simulator_queue, analyzer_queue=None, next_robot_id=1):
        super().__init__(conf, simulator_queue, analyzer_queue, next_robot_id)
        self.individuals = []

    def init_pop(self, recovered_individuals=None):
        """
        Populates the population (individuals list) with Individual objects that contains their respective genotype.
        """
        recovered_individuals = [] if recovered_individuals is None else recovered_individuals
        for i in range(self.config.population_size - len(recovered_individuals)):
            print("create individual")
            individual = self._new_individual(
                self.config.genotype_constructor(self.config.genotype_conf, self.next_robot_id))
            self.individuals.append(individual)
            self.next_robot_id += 1
        self.individuals = recovered_individuals + self.individuals

    def _new_individual(self, genotype,
                        parents: Optional[List[Individual]] = None):
        individual = Individual(genotype)
        individual.develop()
        return individual


def main():
    # experiment params #
    num_generations = 100
    population_size = 100
    offspring_size = 200
    genotype_conf = PlasticodingConfig(
        max_structural_modules=20,
        # max_joints=10,
    )
    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=genotype_conf,
    )
    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
    )
    # experiment params #
    # Parse command line / file input arguments
    gen_num = 0
    next_robot_id = 1
    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity,
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 4),
        parent_selection=lambda individuals: multiple_selection(individuals, 4, tournament_selection),
        population_management=NSGA2,
        population_management_selector=None,
        evaluation_time=0,
        offspring_size=offspring_size,
        experiment_name="test",
        experiment_management=None,
    )
    population = MockPopulation(population_conf, None, None, next_robot_id)
    population.init_pop()
    offspring = []
    for i in range(population_conf.offspring_size):
        individual = Individual(population_conf.genotype_constructor(population_conf.genotype_conf, 0))
        individual.develop()
        offspring.append(individual)

    def initialize_fitness(individuals):
        d3_enabled: bool = False
        for individual in individuals:
            theta = np.random.uniform(0, math.pi / 2)
            omega = np.random.uniform(0, math.pi / 2)
            r = np.random.uniform(0.5, 1)
            if d3_enabled:
                individual.objectives = [r * np.cos(theta) * np.cos(omega),
                                         r * np.sin(theta),
                                         r * np.cos(theta) * np.sin(omega)]
            else:
                individual.objectives = [r * np.cos(theta),
                                         r * np.sin(theta)]

    initialize_fitness(population.individuals)
    initialize_fitness(offspring)
    survived_individuals = NSGA2(population.individuals, offspring, debug=True)
    plt.show()


if __name__ == "__main__":
    main()
