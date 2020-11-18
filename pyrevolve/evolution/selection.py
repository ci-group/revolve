from __future__ import annotations
from random import randint

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import List, Callable
    from pyrevolve.evolution.individual import Individual


_neg_inf = -float('Inf')


def _compare_maj_fitness(indiv_1, indiv_2):
    fit_1 = _neg_inf if indiv_1.fitness is None else indiv_1.fitness
    fit_2 = _neg_inf if indiv_2.fitness is None else indiv_2.fitness
    return fit_1 > fit_2


def tournament_selection(population: List[Individual], k=2) -> Individual:
    """
    Perform tournament selection and return best individual
    :param population: list of individuals where to select from
    :param k: amount of individuals to participate in tournament
    """
    best_individual = None
    for _ in range(k):
        individual = population[randint(0, len(population) - 1)]
        if (best_individual is None) or (_compare_maj_fitness(individual, best_individual)):
            best_individual = individual
    return best_individual


def multiple_selection(population: List[Individual],
                       selection_size: int,
                       selection_function: Callable[[List[Individual]], Individual]
                       ) -> List[Individual]:
    """
    Perform selection on population of distinct group, it can be used in the
    form parent selection or survival selection.
    It never selects the same individual more than once
    :param population: list of individuals where to select from
    :param selection_size: amount of individuals to select
    :param selection_function:
    """
    if len(population) < selection_size:
        print("selection problem: population " + str(len(population)) + " - selection size " + str(selection_size))
        assert (len(population) >= selection_size)

    selected_individuals = []
    for _ in range(selection_size):
        new_individual = False
        while new_individual is False:
            selected_individual = selection_function(population)
            if selected_individual not in selected_individuals:
                selected_individuals.append(selected_individual)
                new_individual = True
    return selected_individuals


def multiple_selection_with_duplicates(population: List[Individual],
                                       selection_size: int,
                                       selection_function: Callable[[List[Individual]], Individual]
                                       ) -> List[Individual]:
    """
    Perform selection on population of distinct group, it can be used in the
    form parent selection or survival selection.
    It can select the same individual more than once
    :param population: list of individuals where to select from
    :param selection_size: amount of individuals to select
    :param selection_function:
    """
    selected_individuals = []
    for _ in range(selection_size):
        selected_individual = selection_function(population)
        selected_individuals.append(selected_individual)
    return selected_individuals
