from __future__ import absolute_import, unicode_literals
import asyncio
import time
import subprocess
import os, sys
import random
from pycelery.converter import args_to_dic, dic_to_args, args_default
from pyrevolve import revolve_bot, parser
from pycelery.celerycontroller import CeleryController
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
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.custom_logging.logger import logger


async def run():
    """A revolve manager that is using celery for task execution."""
    begin = time.time()
    initiation = 0
    
    settings = parser.parse_args()

    celerycontroller = CeleryController(settings) # Starting celery

    await asyncio.sleep(max(settings.n_cores,10)) # Celery needs time

    # experiment params #
    num_generations = 50
    population_size = 100
    offspring_size = 50

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
    # experiment params #

    experiment_management = ExperimentManagement(settings)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)

    if do_recovery:
        gen_num, has_offspring, next_robot_id = experiment_management.read_recovery_state(population_size, offspring_size)

        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            await celerycontroller.shutdown()
            return
    else:
        gen_num = 0
        next_robot_id = 1

    # Start gazebos!
    await celerycontroller.start_gazebo_instances()

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=random_initialization,
        genotype_conf=genotype_conf,
        fitness_function='displacement_velocity', # Celery will evaluate the string into a function
        mutation_operator=standard_mutation,
        mutation_conf=mutation_conf,
        crossover_operator=standard_crossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
        celery = True
    )

    analyzer_queue = None
    population = Population(population_conf, celerycontroller, analyzer_queue, next_robot_id)

    if do_recovery:
        # loading a previous state of the experiment
        await population.load_snapshot(gen_num)
        if gen_num >= 0:
            logger.info('Recovered snapshot '+str(gen_num)+', pop with ' + str(len(population.individuals))+' individuals')
        if has_offspring:
            individuals = await population.load_offspring(gen_num, population_size, offspring_size, next_robot_id)
            gen_num += 1
            logger.info('Recovered unfinished offspring '+str(gen_num))

            if gen_num == 0:
                await population.init_pop(individuals)
            else:
                population = await population.next_gen(gen_num, individuals)

    else:
        # starting a new experiment
        experiment_management.create_exp_folders()
        end1 = time.time()
        initiation = end1-begin

        await population.init_pop()

    while gen_num < num_generations-1:
        gen_num += 1

        population = await population.next_gen(gen_num)

        # reset gazebo and celery if something went wrong or every 10 generations
        # if population.conf.celery_reboot:
        #    await celerycontroller.reset_celery()
        #    population.conf.celery_reboot = False}

    end = time.time()
    f = open("speed.txt", "a")
    f.write("---------------")
    f.write(f"runtime: {end-begin} on {settings.n_cores} cores. Gen: {num_generations}, Population: {population_size}, Offspring: {offspring_size}\n")
    f.write(f"init took: {initiation}")
    f.write(f"generation_time: {population_conf.generation_time} \n")
    f.write(f"generation init time: {population_conf.generation_init} \n")
    f.write(f"generation fin time: {population_conf.generational_fin}\n ")
    f.close()

    """Uncomment this if you want the manager to close celery and gazebo"""
    await celerycontroller.shutdown()
