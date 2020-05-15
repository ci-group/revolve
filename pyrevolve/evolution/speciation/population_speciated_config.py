from __future__ import annotations
from ..population.population_config import PopulationConfig

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable, Optional, List, Union
    from pyrevolve.evolution.individual import Individual
    from pyrevolve.genotype import Genotype
    from pyrevolve.revolve_bot import RevolveBot
    from pyrevolve.tol.manage.robotmanager import RobotManager


class PopulationSpeciatedConfig(PopulationConfig):
    DEFAULT_YOUNG_AGE_THRESHOLD: int = 5
    DEFAULT_YOUNG_AGE_FITNESS_BOOST: float = 1.1
    DEFAULT_OLD_AGE_THRESHOLD: int = 30,
    DEFAULT_OLD_AGE_FITNESS_PENALTY: float = 0.5
    DEFAULT_SPECIES_MAX_STAGNATION: int = 50,
    DEFAULT_OFFSPRING_SIZE: Optional[int] = None

    # TODO reorder arguments
    def __init__(self,
                 population_size: int,
                 genotype_constructor: Callable[[object, int], Genotype],
                 genotype_conf: object,
                 fitness_function: Callable[[RobotManager, RevolveBot], float],
                 mutation_operator: Callable[[Genotype, object], Genotype],
                 mutation_conf: object,
                 crossover_operator: Callable[[List[Individual], object, object], Genotype],
                 crossover_conf: object,
                 selection: Callable[[List[Individual]], Individual],
                 parent_selection: Callable[[List[Individual]], List[Individual]],
                 population_management: Callable[
                     [List[Individual], List[Individual], Callable[[List[Individual]], Individual]],
                     List[Individual]
                 ],
                 population_management_selector: Callable[[List[Individual]], Individual],
                 evaluation_time: float,
                 experiment_name: str,
                 experiment_management,
                 are_individuals_compatible_fn: Callable[[Individual, Individual], bool],
                 young_age_threshold: int = DEFAULT_YOUNG_AGE_THRESHOLD,
                 young_age_fitness_boost: float = DEFAULT_YOUNG_AGE_FITNESS_BOOST,
                 old_age_threshold: int = DEFAULT_OLD_AGE_THRESHOLD,
                 old_age_fitness_penalty: float = DEFAULT_OLD_AGE_FITNESS_PENALTY,
                 species_max_stagnation: int = DEFAULT_SPECIES_MAX_STAGNATION,
                 offspring_size: Optional[int] = DEFAULT_OFFSPRING_SIZE):
        """
        Creates a PopulationSpeciatedConfig object that sets the particular configuration for the population with species

        :param population_size: size of the population
        :param genotype_constructor: class of the genotype used.
            First parameter is the config of the genome.
            Second is the id of the genome
        :param genotype_conf: configuration for genotype constructor
        :param fitness_function: function that takes in a `RobotManager` as a parameter and produces a fitness for the robot
        :param mutation_operator: operator to be used in mutation
        :param mutation_conf: configuration for mutation operator
        :param crossover_operator: operator to be used in crossover.
            First parameter is the list of parents (usually 2).
            Second parameter is the Genotype Conf
            Third parameter is Crossover Conf
        :param selection: selection type
        :param parent_selection: selection type during parent selection
        :param population_management: type of population management ie. steady state or generational
        :param evaluation_time: duration of an experiment
        :param experiment_name: name for the folder of the current experiment
        :param experiment_management: object with methods for managing the current experiment
        :param are_individuals_compatible_fn: function that determines if two individuals are compatible
        :param young_age_threshold: define until what age (excluded) species are still young
            and need to be protected (with a fitness boost)
        :param young_age_fitness_boost: Fitness multiplier for young species.
            Make sure it is > 1.0 to avoid confusion
        :param old_age_threshold: define from what age (excluded) species start to be considered old
            and need to be penalized (the best species is forcefully kept young - age 0)
        :param old_age_fitness_penalty: Fitness multiplier for old species.
            Make sure it is < 1.0 to avoid confusion.
        :param species_max_stagnation: maximum number of iterations without improvement of the species.
        :param offspring_size (optional): size of offspring (for steady state)
        """
        super().__init__(population_size,
                         genotype_constructor,
                         genotype_conf,
                         fitness_function,
                         mutation_operator,
                         mutation_conf,
                         crossover_operator,
                         crossover_conf,
                         selection,
                         parent_selection,
                         population_management,
                         population_management_selector,
                         evaluation_time,
                         experiment_name,
                         experiment_management,
                         offspring_size)
        self.are_individuals_compatible = are_individuals_compatible_fn  # type: Callable[[Individual, Individual], bool]
        self.young_age_threshold = young_age_threshold
        self.young_age_fitness_boost = young_age_fitness_boost
        self.old_age_threshold = old_age_threshold
        self.old_age_fitness_penalty = old_age_fitness_penalty
        self.species_max_stagnation = species_max_stagnation

    @staticmethod
    def from_population_config(
            population_config: Union[PopulationConfig, PopulationSpeciatedConfig],
            are_individuals_compatible_fn: Optional[Callable[[Individual, Individual], bool]] = None,
            young_age_threshold: int = DEFAULT_YOUNG_AGE_THRESHOLD,
            young_age_fitness_boost: float = DEFAULT_YOUNG_AGE_FITNESS_BOOST,
            old_age_threshold: int = DEFAULT_OLD_AGE_THRESHOLD,
            old_age_fitness_penalty: float = DEFAULT_OLD_AGE_FITNESS_PENALTY,
            species_max_stagnation: int = DEFAULT_SPECIES_MAX_STAGNATION) -> PopulationSpeciatedConfig:
        """
        Transforms the population config into a population_speciated_config.
        If the argument `population_config` passed in is already a `PopulationSpeciatedConfig`,
        nothing happens and the argument is returned as it is.

        :param population_config: PopulationConfig to test and possibly convert
        :param are_individuals_compatible_fn: parameter for PopulationSpeciatedConfig constructor
            in case of conversion [refer to constructor for meaning]
        :param young_age_threshold: parameter for PopulationSpeciatedConfig constructor
            in case of conversion [refer to constructor for meaning]
        :param young_age_fitness_boost: parameter for PopulationSpeciatedConfig constructor
            in case of conversion [refer to constructor for meaning]
        :param old_age_threshold: parameter for PopulationSpeciatedConfig constructor
            in case of conversion [refer to constructor for meaning]
        :param old_age_fitness_penalty: parameter for PopulationSpeciatedConfig constructor
            in case of conversion [refer to constructor for meaning]
        :param species_max_stagnation: parameter for PopulationSpeciatedConfig constructor
            in case of conversion [refer to constructor for meaning]
        :return: the population config ensured to be of type `PopulationSpeciatedConfig`
        :raises AttributeError: if the `population_config` param cannot be converted to `PopulationSpeciatedConfig`
        """
        if isinstance(population_config, PopulationSpeciatedConfig):
            return population_config
        elif isinstance(population_config, PopulationConfig):
            if are_individuals_compatible_fn is None:
                raise AttributeError("`PopulationSpeciated` is upgrading to `PopulationSpeciatedConfig` "
                                     "but the parameter `are_individuals_compatible_fn` is not specified")
            return PopulationSpeciatedConfig(
                population_size=population_config.population_size,
                genotype_constructor=population_config.genotype_constructor,
                genotype_conf=population_config.genotype_conf,
                fitness_function=population_config.fitness_function,
                mutation_operator=population_config.mutation_operator,
                mutation_conf=population_config.mutation_conf,
                crossover_operator=population_config.crossover_operator,
                crossover_conf=population_config.crossover_conf,
                selection=population_config.selection,
                parent_selection=population_config.parent_selection,
                population_management=population_config.population_management,
                population_management_selector=population_config.population_management_selector,
                evaluation_time=population_config.evaluation_time,
                experiment_name=population_config.experiment_name,
                experiment_management=population_config.experiment_management,
                offspring_size=population_config.offspring_size,
                are_individuals_compatible_fn=are_individuals_compatible_fn,
                young_age_threshold=young_age_threshold,
                young_age_fitness_boost=young_age_fitness_boost,
                old_age_threshold=old_age_threshold,
                old_age_fitness_penalty=old_age_fitness_penalty,
                species_max_stagnation=species_max_stagnation,
            )
        else:
            raise AttributeError(f"PopulationSpeciatedConfig config cannot be created from {type(population_config)}")

