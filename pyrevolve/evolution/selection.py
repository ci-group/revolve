from random import randint


def tournament_selection(population, k=2):
    """
    Perform tournament selection and return best individual
    :param k: amount of individuals to participate in tournament
    """
    assert (population is not None)
    assert (k > 0)

    def is_best_fitness(individual, best_individual):
        assert (individual is not None)
        assert (best_individual is not None)

        _neg_inf = -float('Inf')

        fit_1 = _neg_inf if individual.fitness is None else individual.fitness
        fit_2 = _neg_inf if best_individual.fitness is None else best_individual.fitness
        return fit_1 > fit_2

    best_individual = None
    for _ in range(k):
        individual = population[randint(0, len(population) - 1)]
        if (best_individual is None) or (is_best_fitness(individual, best_individual)):
            best_individual = individual

    return best_individual


def multiple_selection(population, selection_size, selection_function):
    assert (population is not None)
    assert (selection_function is not None)

    assert (selection_size > 0)
    assert (len(population) >= selection_size)
    """
    Perform selection on population of distinct group, can be used in the form parent selection or survival selection
    :param population: parent selection in population
    :param selection_size: amount of indivuals to select
    :param selection_function:
    """

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
