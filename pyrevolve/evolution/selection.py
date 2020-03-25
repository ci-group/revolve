from random import randint

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Callable
    from pyrevolve.evolution.individual import Individual



def is_better_fitness(current: Individual, other: Individual):
    return get_fitness(current) > get_fitness(other)


def get_fitness(individual: Individual):
    assert (individual is not None)
    return -float('Inf') if individual.fitness is None else individual.fitness


def tournament_selection(population: List[Individual], selection_size: int = 2) -> Individual:
    """
    Perform tournament selection and return best individual
    :param population: list of individuals where to select from
    :param selection_size: amount of individuals to participate in tournament
    """
    assert (population is not None)
    assert (selection_size > 0)

    best_individual = None
    for _ in range(selection_size):
        individual = population[randint(0, len(population) - 1)]
        if (best_individual is None) or (is_better_fitness(individual, best_individual)):
            best_individual = individual

    return best_individual


def multiple_selection(population: List[Individual],
                       selection_size: int,
                       selection_function: Callable[[List[Individual]], Individual]) -> List[Individual]:
    """
    Perform selection on population of distinct group, can be used in the form parent selection or survival selection
    :param population: list of individuals where to select from
    :param selection_size: amount of indivuals to select
    :param selection_function:
    """

    assert (population is not None)
    assert (selection_function is not None)

    assert (selection_size > 0)
    assert (len(population) >= selection_size)

    selected_individuals = []
    for _ in range(selection_size):
        new_individual = False
        while new_individual is False:
            selected_individual = selection_function(population)
            if selected_individual not in selected_individuals:
                selected_individuals.append(selected_individual)
                new_individual = True

    assert (len(selected_individuals) == selection_size)

    return selected_individuals

