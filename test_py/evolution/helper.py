import random

from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.evolution.population.population import Population, PopulationConfig
from pyrevolve.evolution.speciation.population_speciated import Speciation, SpeciationConfig
from pyrevolve.evolution.population.population_management import steady_state_population_management
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


def get_lsystem_config():
    body_config = PlasticodingConfig(
        max_structural_modules=20,
        allow_vertical_brick=False,
        use_movement_commands=False,
        use_rotation_commands=False,
        use_movement_stack=True,
    )
    brain_config = NeatBrainGenomeConfig()
    lsystem_config = LSystemCPGHyperNEATGenotypeConfig(body_config, brain_config)
    return body_config, brain_config, lsystem_config


def get_genotype():
    body_config, brain_config, lsystem_config = get_lsystem_config()
    return LSystemCPGHyperNEATGenotype(lsystem_config, 0)

def get_population(random_fitness = False):
    # experiment params #
    num_generations = 200
    population_size = 100
    offspring_size = 50

    body_config, brain_config, lsystem_config = get_lsystem_config()

    plasticMutation_conf = plasticMutationConfig(
        mutation_prob=0.8,
        genotype_conf=body_config
    )

    lmutation_conf = lMutationConfig(
        plasticoding_mutation_conf=plasticMutation_conf,
        neat_conf=brain_config,
    )

    crossover_conf = lCrossoverConfig(
        crossover_prob=0.0,
    )
    # experiment params #

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)

    if do_recovery:
        gen_num, has_offspring = experiment_management.read_recovery_state(population_size, offspring_size)

        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0

    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=LSystemCPGHyperNEATGenotype,
        genotype_conf=lsystem_config,
        fitness_function=fitness.displacement_velocity,
        mutation_operator=lmutation,
        mutation_conf=lmutation_conf,
        crossover_operator=lcrossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management
    )

    n_cores = settings.n_cores

    settings = parser.parse_args()
    simulator_queue = SimulatorQueue(n_cores, settings, settings.port_start)
    analyzer_queue = AnalyzerQueue(1, settings, settings.port_start+n_cores)

    population = Population(population_conf)

    if random_fitness:
        for individual in population.individuals:
            individual.fitness = random.random()

    return population

def get_population_speciated(random_fitness = False):
    # experiment params #
    num_generations = 200
    population_size = 100
    offspring_size = 50

    body_config, brain_config, lsystem_config = get_lsystem_config()

    plasticMutation_conf = plasticMutationConfig(
        mutation_prob=0.8,
        genotype_conf=body_config
    )

    lmutation_conf = lMutationConfig(
        plasticoding_mutation_conf=plasticMutation_conf,
        neat_conf=brain_config,
    )

    crossover_conf = lCrossoverConfig(
        crossover_prob=0.0,
    )
    # experiment params #

    # Parse command line / file input arguments
    settings = parser.parse_args()
    experiment_management = ExperimentManagement(settings)
    do_recovery = settings.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info('Activated run '+settings.run+' of experiment '+settings.experiment_name)

    if do_recovery:
        gen_num, has_offspring = experiment_management.read_recovery_state(population_size, offspring_size)

        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0

    are_genomes_compatible_fn = None        # TODO
    young_age_threshold: int = 0            # TODO
    young_age_fitness_boost: float = 0.0    # TODO
    old_age_threshold: int = 0              # TODO
    old_age_fitness_penalty: float = 0.0    # TODO

    population_conf = SpeciationConfig(
        population_size=population_size,
        genotype_constructor=LSystemCPGHyperNEATGenotype,
        genotype_conf=lsystem_config,
        fitness_function=fitness.displacement_velocity,
        mutation_operator=lmutation,
        mutation_conf=lmutation_conf,
        crossover_operator=lcrossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(individuals, 2, tournament_selection),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
        are_genomes_compatible_fn=are_genomes_compatible_fn,
        young_age_threshold=young_age_threshold,
        young_age_fitness_boost=young_age_fitness_boost,
        old_age_threshold=old_age_threshold,
        old_age_fitness_penalty=old_age_fitness_penalty,
    )

    n_cores = settings.n_cores

    settings = parser.parse_args()
    simulator_queue = SimulatorQueue(n_cores, settings, settings.port_start)
    analyzer_queue = AnalyzerQueue(1, settings, settings.port_start+n_cores)

    population = Speciation(population_conf, simulator_queue, analyzer_queue)

    if random_fitness:
        for individual in population.individuals:
            individual.fitness = random.random()

    return population

