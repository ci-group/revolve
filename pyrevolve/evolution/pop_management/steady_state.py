from pyrevolve.evolution.selection import multiple_selection


def steady_state_population_management(old_individuals, new_individuals, selector):
    pop_size = len(old_individuals)
    selection_pool = old_individuals + new_individuals

    return multiple_selection(selection_pool, pop_size, selector)
