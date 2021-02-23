import random

_neg_inf = -float('Inf')


def _compare_maj_fitness(indiv_1, indiv_2, environments):
    final_season = list(environments.keys())[-1]

    fit_1 = indiv_1[final_season].consolidated_fitness
    fit_2 = indiv_2[final_season].consolidated_fitness

    fit_1 = _neg_inf if fit_1 is None else fit_1
    fit_2 = _neg_inf if fit_2 is None else fit_2

    return fit_1 > fit_2


def tournament_selection(population, environments, k=2):
    """
    Perform tournament selection and return best individual
    :param k: amount of individuals to participate in tournament
    """
    best_individual = None
    for _ in range(k):
        individual = population[random.randint(0, len(population) - 1)]
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

def ranking_selection(old_population, offspring, environment):

    old_pop_filtered = [individual for individual in old_population
                        if individual[environment].fitness is not None]
    offspring_filtered = [individual for individual in offspring
                          if individual[environment].fitness is not None]
    population = old_pop_filtered + offspring_filtered

    ranked_population = sorted(population, key=lambda x: x[environment].fitness)

    def linear_ranking(_rank, pop_size):
        return _rank / (pop_size-1)

    probabilities = []
    for rank, individual in enumerate(ranked_population):
        individual[environment].early_survival_probability = linear_ranking(rank, len(ranked_population))
        probabilities.append(individual[environment].early_survival_probability)

    selected_offspring = []
    for individual in offspring:
        if individual[environment].early_survival_probability >= random.uniform(0, 1):
            selected_offspring.append(individual)

    return selected_offspring


# def ranking_selection(old_population, offspring, environment):
#
#     old_pop_filtered = [individual for individual in old_population
#                         if individual[environment].fitness is not None]
#     offspring_filtered = [individual for individual in offspring
#                           if individual[environment].fitness is not None]
#     population = old_pop_filtered + offspring_filtered
#
#     ranked_population = sorted(population, key=lambda x: x[environment].fitness)
#
#     def linear_ranking(_rank, pop_size):
#         if _rank == 0:
#             return 0
#         else:
#             rank_range = sum(list(range(0, pop_size , 1)))
#             return _rank / rank_range
#
#     probabilities = []
#     for rank, individual in enumerate(ranked_population):
#         individual[environment].early_survival_probability = linear_ranking(rank, len(ranked_population))
#         probabilities.append(individual[environment].early_survival_probability)
#
#     selected_offspring = []
#     for individual in offspring:
#         if individual[environment].early_survival_probability >= random.uniform(min(probabilities), max(probabilities)):
#             selected_offspring.append(individual)
#
#     return selected_offspring