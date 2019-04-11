def steady_state_population_management(old_individuals, new_individuals, selector):
	pop_size = len(old_individuals)
	selection_pool = old_individuals + new_individuals
	selected_individuals = []
	for _i in range(pop_size):
		selected = selector(selection_pool)
		selected_individuals.append(selected)

	return selected_individuals
