#!/usr/bin/env python3
from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.speciation.population_speciated import Speciation, SpeciationConfig
from pyrevolve.evolution.population import create_population_mediator, steady_state_population_management
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.lsystem_neat.crossover import CrossoverConfig as lCrossoverConfig
from pyrevolve.genotype.lsystem_neat.crossover import standard_crossover as lcrossover
from pyrevolve.genotype.lsystem_neat.mutation import LSystemNeatMutationConf as lMutationConfig
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig as plasticMutationConfig
from pyrevolve.genotype.lsystem_neat.mutation import standard_mutation as lmutation

from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue
from pyrevolve.custom_logging.logger import logger
from pyrevolve.genotype.plasticoding import PlasticodingConfig
from pyrevolve.genotype.lsystem_neat.lsystem_neat_genotype import LSystemCPGHyperNEATGenotype, LSystemCPGHyperNEATGenotypeConfig
from pyrevolve.genotype.neat_brain_genome.neat_brain_genome import NeatBrainGenomeConfig

from pyrevolve.util.generation import Generation


async def run():
    """
    The main coroutine, which is started below.
    """
    # experiment params #
    number_of_generations = 200
    population_size = 100
    offspring_size = 50

    body_conf = PlasticodingConfig(
        max_structural_modules=20,
        allow_vertical_brick=False,
        use_movement_commands=False,
        use_rotation_commands=False,
        use_movement_stack=True,
    )
    brain_config = NeatBrainGenomeConfig()
    lsystem_config = LSystemCPGHyperNEATGenotypeConfig(body_conf, brain_config)

    plasticMutation_config = plasticMutationConfig(mutation_prob=0.8, genotype_conf=body_conf)

    lmutation_config = lMutationConfig(
        plasticoding_mutation_conf=plasticMutation_config,
        neat_conf=brain_config,
    )

    crossover_config = lCrossoverConfig(
        crossover_prob=0.0,
    )
    # experiment params #

    are_genomes_compatible_fn = None        # TODO
    young_age_threshold: int = 0            # TODO
    young_age_fitness_boost: float = 0.0    # TODO
    old_age_threshold: int = 0              # TODO
    old_age_fitness_penalty: float = 0.0    # TODO

    # TODO population factory

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)

    logger.info('Activated run ' + settings.run + ' of experiment ' + settings.experiment_name)

    # TODO population config reform required
    population_config = SpeciationConfig(
        population_size=population_size,
        genotype_constructor=LSystemCPGHyperNEATGenotype,
        genotype_conf=lsystem_config,
        fitness_function=fitness.displacement_velocity,
        mutation_operator=lmutation,
        mutation_conf=lmutation_config,
        crossover_operator=lcrossover,
        crossover_conf=crossover_config,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        are_genomes_compatible_fn=are_genomes_compatible_fn,
        young_age_threshold=young_age_threshold,
        young_age_fitness_boost=young_age_fitness_boost,
        old_age_threshold=old_age_threshold,
        old_age_fitness_penalty=old_age_fitness_penalty,
    )

    n_cores = settings.n_cores
    settings = parser.parse_args()
    simulator_queue = SimulatorQueue(n_cores, settings, settings.port_start)
    await simulator_queue.start()

    analyzer_queue = AnalyzerQueue(1, settings, settings.port_start + n_cores)
    await analyzer_queue.start()

    generation = Generation(number_of_generations)
    recover_population = settings.recovery_enabled and not experiment_management.experiment_is_new()
    population_mediator = await create_population_mediator(population_config, simulator_queue, analyzer_queue, recover_population)

    while not generation.done():
        #TODO why increment before doing the step?
        generation.increment()

        population = await population_mediator.next_generation()
        experiment_management.export_snapshots(population.individuals)
