#!/usr/bin/env python3
import asyncio
​
from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population import Population, PopulationConfig
from pyrevolve.evolution.pop_management.steady_state import steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement

# from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
# from pyrevolve.genotype.plasticoding.crossover.standard_crossover import standard_crossover
# from pyrevolve.genotype.plasticoding.initialization import random_initialization
# from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
# from pyrevolve.genotype.plasticoding.mutation.standard_mutation import standard_mutation
from pyrevolve.genotype.plasticoding.plasticoding import PlasticodingConfig
​
from pyrevolve.genotype.lsystem_neat.lsystem_neat_genotype import LSystemCPGHyperNEATGenotype, LSystemCPGHyperNEATGenotypeConfig
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.custom_logging.logger import logger
from pyrevolve.genotype.plasticoding.initialization import random_initialization
from pyrevolve.genotype.lsystem_neat.mutation import standard_mutation, LSystemNeatCrossoverConf
from pyrevolve.genotype.lsystem_neat.crossover import standard_crossover
​
​
async def run():
    """
    The main coroutine, which is started below.
    """
​
    # experiment params #
body_conf = PlasticodingConfig()
brain_conf = NeatBrainGenomeConfig()
lsystem_conf = LSystemCPGHyperNEATGenotypeConfig(body_conf, brain_conf)  # genotype_conf

robot_id = 105
population_size = 4
offspring_size = 2
individuals = []  # Population.individuals

crossover_operator = Lcrossover
crossover_conf = LCrossoverConfig(0.8)

plasticoding_mutation = MutationConfig(
    mutation_prob=0.8,
    genotype_conf=body_conf,
)

mutation_operator = LMutation
mutation_conf = LMutationConfig(plasticoding_mutation, brain_conf)

# experiment params #
​
    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()
​
    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)
​
    if do_recovery:
        gen_num, has_offspring, next_robot_id = experiment_management.read_recovery_state(population_size, offspring_size)
​
        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0
        next_robot_id = 1
​
population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=random_gramar_initialization,
        genotype_conf=lsystem_conf,
        fitness_function=fitness.displacement_velocity,
        mutation_operator=LMutation,
        mutation_conf=mutation_conf,
        crossover_operator=Lcrossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
    )
​
    n_cores = settings.n_cores
​
    settings = parser.parse_args()
    simulator_queue = SimulatorQueue(n_cores, settings, settings.port_start)
    await simulator_queue.start()
​
    analyzer_queue = AnalyzerQueue(1, settings, settings.port_start+n_cores)
    await analyzer_queue.start()
​
    population = Population(population_conf, simulator_queue, analyzer_queue, next_robot_id)
​
    if do_recovery:
        # loading a previous state of the experiment
        await population.load_snapshot(gen_num)
        if gen_num >= 0:
            logger.info('Recovered snapshot '+str(gen_num)+', pop with ' + str(len(population.individuals))+' individuals')
        if has_offspring:
            individuals = await population.load_offspring(gen_num, population_size, offspring_size, next_robot_id)
            gen_num += 1
            logger.info('Recovered unfinished offspring '+str(gen_num))
​
            if gen_num == 0:
                await population.init_pop(individuals)
            else:
                population = await population.next_gen(gen_num, individuals)
​
            experiment_management.export_snapshots(population.individuals, gen_num)
    else:
        # starting a new experiment
        experiment_management.create_exp_folders()
        await population.init_pop()
        experiment_management.export_snapshots(population.individuals, gen_num)
​

    # output result after completing all generations...