#!/usr/bin/env python3
import math
from dataclasses import dataclass

import multineat
from pyrevolve import parser
from pyrevolve.custom_logging.logger import logger
from pyrevolve.evolution.fitness import follow_line as fitness_follow_line
from pyrevolve.evolution.population.population import Population
from pyrevolve.evolution.population.population_config import PopulationConfig
from pyrevolve.evolution.population.population_management import (
    steady_state_population_management,
)
from pyrevolve.evolution.selection import multiple_selection, tournament_selection
from pyrevolve.experiment_management import ExperimentManagement
from pyrevolve.genotype.bodybrain_composition.config import (
    Config as BodybrainCompositionConfig,
)
from pyrevolve.genotype.bodybrain_composition.crossover import (
    crossover as bodybrain_composition_crossover,
)
from pyrevolve.genotype.bodybrain_composition.genotype import (
    Genotype as BodybrainCompositionGenotype,
)
from pyrevolve.genotype.bodybrain_composition.mutation import (
    mutate as bodybrain_composition_mutate,
)
from pyrevolve.genotype.cppnneat.brain.config import Config as CppnneatBrainConfig
from pyrevolve.genotype.cppnneat.brain.crossover import (
    crossover as cppnneat_brain_crossover,
)
from pyrevolve.genotype.cppnneat.brain.develop import develop as cppnneat_brain_develop
from pyrevolve.genotype.cppnneat.brain.genotype import Genotype as CppnneatBrainGenotype
from pyrevolve.genotype.cppnneat.brain.mutation import mutate as cppnneat_brain_mutate
from pyrevolve.genotype.cppnneat.config import get_default_multineat_params
from pyrevolve.genotype.learning_body.config import Config as LearningBodyConfig
from pyrevolve.genotype.learning_body.crossover import (
    crossover as learning_body_crossover,
)
from pyrevolve.genotype.learning_body.develop import develop as learning_body_develop
from pyrevolve.genotype.learning_body.genotype import Genotype as LearningBodyGenotype
from pyrevolve.genotype.learning_body.mutation import mutate as learning_body_mutate
from pyrevolve.genotype.plasticoding.crossover.crossover import CrossoverConfig
from pyrevolve.genotype.plasticoding.mutation.mutation import MutationConfig
from pyrevolve.genotype.plasticoding import PlasticodingConfig
from pyrevolve.util.supervisor.analyzer_queue import AnalyzerQueue
from pyrevolve.util.supervisor.simulator_queue import SimulatorQueue


@dataclass
class GenotypeConstructorConfig:
    body_plasticoding_config: None
    brain_n_start_mutations: int
    bodybrain_composition_config: BodybrainCompositionConfig
    brain_multineat_params: multineat.Parameters
    brain_cppn_output_activation_type: multineat.ActivationFunction


robot_path = "babyA.yaml"

def create_random_genotype(
    config: GenotypeConstructorConfig, id: int
) -> BodybrainCompositionGenotype:
    return BodybrainCompositionGenotype[LearningBodyGenotype, CppnneatBrainGenotype](
        id,
        config.bodybrain_composition_config,
        LearningBodyGenotype.random(config),
        CppnneatBrainGenotype.random(
            config.brain_multineat_params,
            config.brain_cppn_output_activation_type,
            config.brain_n_start_mutations,
            config.bodybrain_composition_config.brain_develop_config.innov_db,
            config.bodybrain_composition_config.brain_develop_config.rng,
        ),
    )


async def run():
    """
    The main coroutine, which is started below.
    """

    # experiment params #
    num_generations = 10
    population_size = 10
    offspring_size = 5

    target_distance = 10

    brain_n_start_mutations: int = 10

    # brain multineat settings
    multineat_params_brain = get_default_multineat_params()

    # multineat rng
    rng = multineat.RNG()
    rng.TimeSeed()

    # multineat innovation databases
    innov_db_brain = multineat.InnovationDatabase()

    # config for brain
    brain_config = CppnneatBrainConfig(
        multineat_params=multineat_params_brain,
        innov_db=innov_db_brain,
        rng=rng,
        mate_average=False,
        interspecies_crossover=True,
        abs_output_bound=1.0,
        use_frame_of_reference=True,
        output_signal_factor=1.0,
        range_ub=1.0,
        init_neuron_state=math.sqrt(2) / 2.0,
        reset_neuron_random=False,
    )

    body_config = LearningBodyConfig(
        mutation_prob=0, crossover_prob=0
    )

    # bodybrain composition genotype config
    bodybrain_composition_config = BodybrainCompositionConfig(
        body_crossover=learning_body_crossover,
        brain_crossover=cppnneat_brain_crossover,
        body_crossover_config=body_config,
        brain_crossover_config=brain_config,
        body_mutate=learning_body_mutate,
        brain_mutate=cppnneat_brain_mutate,
        body_mutate_config=body_config,
        brain_mutate_config=brain_config,
        body_develop=learning_body_develop,
        brain_develop=cppnneat_brain_develop,
        body_develop_config=robot_path,
        brain_develop_config=brain_config,
    )

    # genotype constructor config. Used by `create_random_genotype` in this file.
    genotype_constructor_config = GenotypeConstructorConfig(
        PlasticodingConfig(
            max_structural_modules=15,
            #plastic=False,
        ),
        brain_n_start_mutations,
        bodybrain_composition_config,
        multineat_params_brain,
        brain_cppn_output_activation_type=multineat.ActivationFunction.TANH,
    )

    # parse command line arguments
    settings = parser.parse_args()

    # create object that provides functionality
    # to access the correct experiment directories,
    # export/import things, recovery info etc.
    experiment_management = ExperimentManagement(settings)

    # settings for the evolutionary process
    population_conf = PopulationConfig(
        population_size=population_size,
        genotype_constructor=create_random_genotype,
        genotype_conf=genotype_constructor_config,
        fitness_function=fitness_follow_line,
        mutation_operator=bodybrain_composition_mutate,
        mutation_conf=bodybrain_composition_config,
        crossover_operator=bodybrain_composition_crossover,
        crossover_conf=bodybrain_composition_config,
        selection=lambda individuals: tournament_selection(individuals, 2),
        parent_selection=lambda individuals: multiple_selection(
            individuals, 2, tournament_selection
        ),
        population_management=steady_state_population_management,
        population_management_selector=tournament_selection,
        evaluation_time=settings.evaluation_time,
        offspring_size=offspring_size,
        experiment_name=settings.experiment_name,
        experiment_management=experiment_management,
        # target_distance=target_distance,
    )

    # check if recovery is required
    do_recovery = (
        settings.recovery_enabled and not experiment_management.experiment_is_new()
    )

    # print some info about the experiment and recovery
    logger.info(
        "Activated run " + settings.run + " of experiment " + settings.experiment_name
    )
    if settings.recovery_enabled:
        if experiment_management.experiment_is_new():
            logger.info("This is a new experiment. No recovery performed.")
        else:
            logger.info("Recovering proviously stopped run")

    # set gen_num and next_robot_id to starting value,
    # or get them from recovery state
    # gen_num will be -1 if nothing has been done yet
    if do_recovery:
        (
            gen_num,
            has_offspring,
            next_robot_id,
            _,
        ) = experiment_management.read_recovery_state(population_size, offspring_size)
    else:
        gen_num = 0
        next_robot_id = 1

    # maybe experiment is done already?
    if gen_num == num_generations - 1:
        logger.info("Experiment is already complete.")
        return

    # setup simulator_quque and analyzer_queue based on number of cores
    n_cores = settings.n_cores

    simulator_queue = SimulatorQueue(n_cores, settings, settings.port_start)
    await simulator_queue.start()

    analyzer_queue = AnalyzerQueue(1, settings, settings.port_start + n_cores)
    await analyzer_queue.start()

    # create start population
    population = Population(
        population_conf, simulator_queue, analyzer_queue, next_robot_id
    )

    # Recover if required
    if do_recovery:
        # loading a previous state of the experiment
        population.load_snapshot(
            gen_num
        )  # I think this breaks when gen_num == -1 --Aart
        if gen_num >= 0:
            logger.info(
                "Recovered snapshot "
                + str(gen_num)
                + ", pop with "
                + str(len(population.individuals))
                + " individuals"
            )
        if has_offspring:
            individuals = population.load_offspring(
                gen_num, population_size, offspring_size, next_robot_id
            )
            gen_num += 1
            logger.info("Recovered unfinished offspring " + str(gen_num))

            if gen_num == 0:
                await population.initialize(individuals)
            else:
                population = await population.next_generation(gen_num, individuals)

            experiment_management.export_snapshots(population.individuals, gen_num)
    else:
        # starting a new experiment
        experiment_management.create_exp_folders()
        await population.initialize()
        experiment_management.export_snapshots(population.individuals, gen_num)

    # our evolutionary loop
    # gen_num can still be -1.
    while gen_num < num_generations - 1:
        gen_num += 1
        population = await population.next_generation(gen_num)
        experiment_management.export_snapshots(population.individuals, gen_num)
