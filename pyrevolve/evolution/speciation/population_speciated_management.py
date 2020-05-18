from pyrevolve.evolution.selection import multiple_selection, multiple_selection_with_duplicates


def steady_state_speciated_population_management(old_individuals, new_individuals, number_of_individuals, selector):
    # Stead state population
    # total size of population is the sum of all the species individuals.
    # TODO old function: need parameter for ...
    selection_pool = old_individuals + new_individuals

    return multiple_selection_with_duplicates(selection_pool, number_of_individuals, selector)


def generational_speciated_population_management(old_individuals, new_individuals, number_of_individuals, selector):
    # Note (old_individuals, number_of_individuals, and selector) are not used,
    # but for the interface to be similar to steady state speciated.
    return new_individuals
