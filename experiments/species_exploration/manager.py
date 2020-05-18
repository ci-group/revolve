#!/usr/bin/env python3
from __future__ import annotations

from pyrevolve import parser
from pyrevolve.evolution import fitness
from pyrevolve.evolution.population.population_management import steady_state_population_management
from pyrevolve.evolution.selection import multiple_selection_with_duplicates, multiple_selection, tournament_selection
from pyrevolve.evolution.speciation.population_speciated import PopulationSpeciated
from pyrevolve.evolution.speciation.population_speciated_config import PopulationSpeciatedConfig
from pyrevolve.evolution.speciation.population_speciated_management import steady_state_speciated_population_management
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
from pyrevolve.revolve_bot.morphology_compatibility import MorphologyCompatibility

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Union
    from pyrevolve.evolution.population.population import Population
    from pyrevolve.evolution.individual import Individual


async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 200
    population_size = 100
    offspring_size = 50
    remove_species_gen_n = 100

    body_conf = PlasticodingConfig(
        max_structural_modules=20,
        allow_vertical_brick=False,
        use_movement_commands=True,
        use_rotation_commands=False,
        use_movement_stack=False,
        allow_joint_joint_attachment=False,
    )
    brain_conf = NeatBrainGenomeConfig()
    brain_conf.multineat_params.DisjointCoeff = 0.3
    brain_conf.multineat_params.ExcessCoeff = 0.3
    brain_conf.multineat_params.WeightDiffCoeff = 0.3
    brain_conf.multineat_params.ActivationADiffCoeff = 0.3
    brain_conf.multineat_params.ActivationBDiffCoeff = 0.3
    brain_conf.multineat_params.TimeConstantDiffCoeff = 0.3
    brain_conf.multineat_params.BiasDiffCoeff = 0.3
    brain_conf.multineat_params.ActivationFunctionDiffCoeff = 0.3
    brain_conf.multineat_params.CompatTreshold = 3.0
    brain_conf.multineat_params.MinCompatTreshold = 3.0
    brain_conf.multineat_params.CompatTresholdModifier = 0.1
    brain_conf.multineat_params.CompatTreshChangeInterval_Generations = 1
    brain_conf.multineat_params.CompatTreshChangeInterval_Evaluations = 1
    genotype_conf = LSystemCPGHyperNEATGenotypeConfig(body_conf, brain_conf)

    plasticMutation_conf = plasticMutationConfig(
        mutation_prob=0.8,
        genotype_conf=body_conf
    )

    lmutation_conf = lMutationConfig(
        plasticoding_mutation_conf=plasticMutation_conf,
        neat_conf=brain_conf,
    )

    crossover_conf = lCrossoverConfig(
        crossover_prob=0.8,
    )

    compatibitity_tester = MorphologyCompatibility(
        total_threshold=1.0,
        size=1.0,
        brick_count=1.0,
        proportion=1.0,
        coverage=1.0,
        joints=1.5,
        branching=1.0,
        symmetry=0.0,
        max_permitted_modules=body_conf.max_structural_modules,
    )

    # experiment params #

    # Parse command line / file input arguments
    args = parser.parse_args()
    experiment_management = ExperimentManagement(args)
    has_offspring = False
    do_recovery = args.recovery_enabled and not experiment_management.experiment_is_new()

    logger.info(f'Activated run {args.run} of experiment {args.experiment_name}')

    if do_recovery:
        #TODO actually, if gen_num > remove_species_gen_n, we should read the recovery state with species=False
        gen_num, has_offspring, next_robot_id, next_species_id = \
            experiment_management.read_recovery_state(population_size, offspring_size, species=True)
        if gen_num == remove_species_gen_n:
            gen_num, has_offspring, next_robot_id, _ = \
                experiment_management.read_recovery_state(population_size, offspring_size, species=False)

        if gen_num == num_generations-1:
            logger.info('Experiment is already complete.')
            return
    else:
        gen_num = 0
        next_robot_id = 1
        next_species_id = 1

    if gen_num < 0:
        logger.info('Experiment continuing from first generation')
        gen_num = 0

    if next_robot_id < 0:
        next_robot_id = 1

    if next_species_id < 0:
        next_species_id = 1

    def are_individuals_brains_compatible_fn(individual1: Individual,
                                             individual2: Individual) -> bool:
        assert isinstance(individual1.genotype, LSystemCPGHyperNEATGenotype)
        assert isinstance(individual2.genotype, LSystemCPGHyperNEATGenotype)
        return individual1.genotype.is_brain_compatible(individual2.genotype, genotype_conf)

    def are_individuals_morphologies_compatible_fn(individual1: Individual,
                                                   individual2: Individual) -> bool:
        return compatibitity_tester.compatible_individuals(individual1, individual2)

    population_conf = PopulationSpeciatedConfig(
        population_size=population_size,
        genotype_constructor=LSystemCPGHyperNEATGenotype,
        genotype_conf=genotype_conf,
        fitness_function=fitness.displacement_velocity,
        mutation_operator=lmutation,
        mutation_conf=lmutation_conf,
        crossover_operator=lcrossover,
        crossover_conf=crossover_conf,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection_with_duplicates(individuals, 2, tournament_selection),
        population_management=steady_state_speciated_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=args.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=args.experiment_name,
        experiment_management=experiment_management,
        # species stuff
        # are_individuals_compatible_fn=are_individuals_brains_compatible_fn,
        are_individuals_compatible_fn=are_individuals_morphologies_compatible_fn,
        young_age_threshold=5,
        young_age_fitness_boost=2.0,
        old_age_threshold=35,
        old_age_fitness_penalty=0.5,
        species_max_stagnation=30,
    )

    def adapt_population_config(config):
        config.population_management = steady_state_population_management
        config.parent_selection = \
            lambda individuals: multiple_selection(individuals, 2, tournament_selection)

    n_cores = args.n_cores

    simulator_queue = SimulatorQueue(n_cores, args, args.port_start)
    await simulator_queue.start()

    analyzer_queue = AnalyzerQueue(1, args, args.port_start+n_cores)
    await analyzer_queue.start()

    population: Union[PopulationSpeciated, Population]
    if gen_num < remove_species_gen_n:
        population = PopulationSpeciated(population_conf,
                                         simulator_queue,
                                         analyzer_queue,
                                         next_robot_id,
                                         next_species_id)
    else:
        population = \
            Population(population_conf,
                       simulator_queue,
                       analyzer_queue,
                       next_robot_id)
        adapt_population_config(population.config)

    if do_recovery:
        # loading a previous state of the experiment
        population.load_snapshot(gen_num)
        if gen_num >= 0:
            logger.info(f'Recovered snapshot {gen_num}, pop with {len(population.genus)} individuals')

        # TODO partial recovery is not implemented, this is a substitute
        has_offspring = False
        next_robot_id = 1 + population.config.population_size + gen_num * population.config.offspring_size
        population.next_robot_id = next_robot_id

        if has_offspring:
            raise NotImplementedError('partial recovery not implemented')
            recovered_individuals = population.load_partially_completed_generation(gen_num, population_size, offspring_size, next_robot_id)
            gen_num += 1
            logger.info(f'Recovered unfinished offspring for generation {gen_num}')

            if gen_num == 0:
                await population.initialize(recovered_individuals)
            else:
                population = await population.next_generation(gen_num, recovered_individuals)

            experiment_management.export_snapshots_species(population.genus, gen_num)
    else:
        # starting a new experiment
        experiment_management.create_exp_folders()
        await population.initialize()
        experiment_management.export_snapshots_species(population.genus, gen_num)

    while gen_num < num_generations-1:
        gen_num += 1
        population = await population.next_generation(gen_num)
        if isinstance(population, PopulationSpeciated):
            experiment_management.export_snapshots_species(population.genus, gen_num)
        else:
            # WARNING: This export_snapshots may need fixing
            experiment_management.export_snapshots(population.individuals, gen_num)

        if gen_num == remove_species_gen_n:
            population = population.into_population()
            # Adjust the configuration
            adapt_population_config(population.config)
            # save the converted population for debugging
            experiment_management.export_snapshots(population.individuals, num_generations + gen_num)
