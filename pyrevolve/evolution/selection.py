from random import randint
import statistics

_neg_inf = -float('Inf')


def _compare_maj_fitness(indiv_1, indiv_2, environments):

    indiv_1_fitness = []
    indiv_2_fitness = []

    for environment in environments:
        indiv_1_fitness.append(indiv_1[environment].fitness)
        indiv_2_fitness.append(indiv_2[environment].fitness)

   # indiv_1_fitness = abs(sum(indiv_1_fitness) - statistics.stdev(indiv_1_fitness))
   # indiv_2_fitness = abs(sum(indiv_2_fitness) - statistics.stdev(indiv_2_fitness))

    indiv_1_fitness = statistics.mean(indiv_1_fitness)
    indiv_2_fitness = statistics.mean(indiv_2_fitness)

    fit_1 = _neg_inf if indiv_1_fitness is None else indiv_1_fitness
    fit_2 = _neg_inf if indiv_2_fitness is None else indiv_2_fitness

    return fit_1 > fit_2


def tournament_selection(population, environments, k=2):
    """
    Perform tournament selection and return best individual
    :param k: amount of individuals to participate in tournament
    """
    best_individual = None
    for _ in range(k):
        individual = population[randint(0, len(population) - 1)]
        if (best_individual is None) or (_compare_maj_fitness(individual, best_individual, environments)):
            best_individual = individual
    return best_individual


def multiple_selection(population, selection_size, selection_function, environments):
    """
    Perform selection on population of distinct group, can be used in the form parent selection or survival selection
    :param population: parent selection in population
    :param selection_size: amount of indivuals to select
    :param selection_function:
    """
    assert (len(population) >= selection_size)
    selected_individuals = []
    for _ in range(selection_size):
        new_individual = False
        while new_individual is False:
            selected_individual = selection_function(population, environments)
            if selected_individual not in selected_individuals:
                selected_individuals.append(selected_individual)
                new_individual = True
    return selected_individuals
