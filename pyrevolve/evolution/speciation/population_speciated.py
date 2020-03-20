from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional, List

    from typing import Callable, Optional, List

    from pyrevolve.genotype import Genotype
    from pyrevolve.revolve_bot import RevolveBot
    from pyrevolve.tol.manage.robotmanager import RobotManager

    from pyrevolve.evolution.population import PopulationConfig
    from pyrevolve.evolution.population.population import Population
    from pyrevolve.evolution.individual import Individual
    from pyrevolve.evolution.speciation.genus import Genus


class PopulationSpeciatedConfig(PopulationConfig):

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
                 are_genomes_compatible_fn: Callable[[Genotype, Genotype], bool],
                 young_age_threshold: int,
                 young_age_fitness_boost: float,
                 old_age_threshold: int,
                 old_age_fitness_penalty: float,
                 offspring_size: Optional[int] = None):
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
        :param are_genomes_compatible_fn: function that determines if two genomes are compatible
        :param young_age_threshold: define until what age (excluded) species are still young
            and need to be protected (with a fitness boost)
        :param young_age_fitness_boost: Fitness multiplier for young species.
            Make sure it is > 1.0 to avoid confusion
        :param old_age_threshold: define from what age (excluded) species start to be considered old
            and need to be penalized (the best species is forcefully kept young - age 0)
        :param old_age_fitness_penalty: Fitness multiplier for old species.
            Make sure it is < 1.0 to avoid confusion.
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

        self.are_genomes_compatible = are_genomes_compatible_fn  # type: Callable[[Genotype, Genotype], bool]

        self.young_age_threshold = young_age_threshold
        self.young_age_fitness_boost = young_age_fitness_boost
        self.old_age_threshold = old_age_threshold
        self.old_age_fitness_penalty = old_age_fitness_penalty


class PopulationSpeciated(Population):

    def __init__(self, config: PopulationSpeciatedConfig, genus: Genus = None):
        super().__init__(config)
        self.individuals = None # TODO Crash when we should use it

        # Genus contains the collection of different species.
        if genus is None:
            self.genus = Genus(config)
        else:
            self.genus = genus
