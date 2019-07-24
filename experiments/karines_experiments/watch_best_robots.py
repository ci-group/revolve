#!/usr/bin/env python3
import asyncio
from pygazebo.pygazebo import DisconnectError

from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
from pyrevolve.util.supervisor.simulator_simple_queue import SimulatorSimpleQueue
import numpy as np


async def run():
    """
    The main coroutine, which is started below.
    """
    # Parse command line / file input arguments


    genotype_conf = PlasticodingConfig(
        max_structural_modules=100,
    )

    mutation_conf = MutationConfig(
        mutation_prob=0.8,
        genotype_conf=genotype_conf,
    )

    crossover_conf = CrossoverConfig(
        crossover_prob=0.8,
    )

    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)

    population_conf = PopulationConfig(
        population_size=100,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity_hill,
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=50,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
        measure_individuals=settings.measure_individuals,
    )

    settings = parser.parse_args()
    simulator_queue = SimulatorSimpleQueue(settings.n_cores, settings, settings.port_start)
    await simulator_queue.start()

    population = Population(population_conf, simulator_queue, 0)

    # choose a snapshot here. and the maximum best individuals you wish to watch
    generation = 99
    max_best = 10
    await population.load_snapshot(generation)

    fitnesses = []
    for ind in population.individuals:
        fitnesses.append(ind.fitness)
    fitnesses = np.array(fitnesses)

    ini = len(population.individuals)-max_best
    fin = len(population.individuals)
    population.individuals = np.array(population.individuals)
    population.individuals = population.individuals[np.argsort(fitnesses)[ini:fin]]

    await population.evaluate(population.individuals, generation)
