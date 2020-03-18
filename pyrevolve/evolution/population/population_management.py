from pyrevolve.evolution.selection import multiple_selection


def steady_state_population_management(old_individuals, new_individuals, selector):
    # Stead state population
    # total size of population is the sum of all the species individuals.
    pop_size = len(old_individuals)
    selection_pool = old_individuals + new_individuals

    return multiple_selection(selection_pool, pop_size, selector)


def generational_population_management(old_individuals, new_individuals):
    assert (len(old_individuals) == len(new_individuals))
    return new_individuals

