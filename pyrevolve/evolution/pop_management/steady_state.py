from pyrevolve.evolution.selection import multiple_selection


def steady_state_population_management(selection_pool, selector, conf):
    pop_size = conf.population_size

    return multiple_selection(selection_pool, pop_size, selector, conf.environments)
