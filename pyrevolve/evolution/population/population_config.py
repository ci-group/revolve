from __future__ import annotations

import sys
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Callable, Optional, List
    from pyrevolve.evolution.individual import Individual
    from pyrevolve.genotype import Genotype
    from pyrevolve.revolve_bot import RevolveBot
    from pyrevolve.tol.manage.robotmanager import RobotManager


class PopulationConfig:
    def __init__(self,
                 population_size: int,
                 genotype_constructor: Callable[[object, int], Genotype],
                 genotype_conf: object,
                 fitness_function: Optional[Callable[[RobotManager, RevolveBot], float]],
                 mutation_operator: Callable[[Genotype, object], Genotype],
                 mutation_conf: object,
                 crossover_operator: Callable[[List[Individual], object, object], Genotype],
                 crossover_conf: object,
                 genotype_test: Callable[[Genotype], bool],
                 selection: Callable[[List[Individual]], Individual],
                 parent_selection: Callable[[List[Individual]], List[Individual]],
                 population_management: Callable[
                     [List[Individual], List[Individual], Callable[[List[Individual]], Individual]],
                     List[Individual]
                 ],
                 population_management_selector: Optional[Callable[[List[Individual]], Individual]],
                 evaluation_time: float,
                 experiment_name: str,
                 experiment_management,
                 offspring_size: Optional[int] = None,
                 grace_time: float = 0.0,
                 objective_functions: Optional[List[Callable[[RobotManager, RevolveBot], float]]] = None,
                 environment_constructor: Optional[Callable[[gymapi.Gym, gymapi.Sim, gymapi.Vec3, gymapi.Vec3, int, gymapi.Env], None]] = None,
                 population_batch_size: int = sys.maxsize):
        """
        Creates a PopulationConfig object that sets the particular configuration for the population

        :param population_size: size of the population
        :param genotype_constructor: class of the genotype used.
            First parameter is the config of the genome.
            Second is the id of the genome
        :param genotype_conf: configuration for genotype constructor
        :param fitness_function: function that takes in a `RobotManager` as a parameter and produces a fitness for
            the robot. Set to `None` if you want to use `objective_functions` instead.
        :param objective_functions: list of functions that takes in a `RobotManager` as a parameter and produces a
            fitness for the robot. This parameter is to be instead of the `fitness_function` when using an algorithm
            that uses multiple objective optimization, like NSGAII.
        :param mutation_operator: operator to be used in mutation
        :param mutation_conf: configuration for mutation operator
        :param crossover_operator: operator to be used in crossover.
            First parameter is the list of parents (usually 2).
            Second parameter is the Genotype Conf
            Third parameter is Crossover Conf
        :param genotype_test: Test for the genotype
        :param selection: selection type
        :param parent_selection: selection type during parent selection
        :param population_management: type of population management ie. steady state or generational
        :param evaluation_time: duration of an evaluation (experiment_time = grace_time + evaluation_time)
        :param experiment_name: name for the folder of the current experiment
        :param experiment_management: object with methods for managing the current experiment
        :param offspring_size (optional): size of offspring (for steady state)
        :param grace_time: time to wait before starting the evaluation (experiment_time = grace_time + evaluation_time), default to 0.0
        :param environment_constructor: optional function that gets called whenever a gym environment is initialized (exclusive to isaac gym)
        :param population_batch_size:
        Function signature is `environment_constructor(gymapi.Gym, gymapi.Sim, gymapi.Vec3, gymapi.Vec3, int, gymapi.Env) -> None`
        """
        # Test if at least one of them is set
        assert fitness_function is not None or objective_functions is not None
        # Test if not both of them are set at the same time
        assert fitness_function is None or objective_functions is None

        self.population_size = population_size
        self.genotype_constructor = genotype_constructor
        self.genotype_conf = genotype_conf
        self.fitness_function = fitness_function
        self.mutation_operator = mutation_operator
        self.mutation_conf = mutation_conf
        self.crossover_operator = crossover_operator
        self.crossover_conf = crossover_conf
        self.genotype_test = genotype_test
        self.selection = selection
        self.parent_selection = parent_selection
        self.population_management = population_management
        self.population_management_selector = population_management_selector
        self.evaluation_time: float = evaluation_time
        self.grace_time: float = grace_time
        self.experiment_name = experiment_name
        self.experiment_management = experiment_management
        self.offspring_size = offspring_size
        self.objective_functions = objective_functions
        self.environment_constructor = environment_constructor
        self.population_batch_size = population_batch_size
