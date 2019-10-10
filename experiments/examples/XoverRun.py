from pyrevolve.evolution.individual import Individual

#Set configuration parts
body_conf = PlasticodingConfig()
brain_conf = NeatBrainGenomeConfig()
lsystem_conf = LSystemCPGHyperNEATGenotypeConfig(body_conf, brain_conf)  #genotype_conf

num_generations = 2
population_size = 4
offspring_size = 2

robot_id = 49
individuals= []

for i in range(population_size):
    LGenotype = LSystemCPGHyperNEATGenotype(lsystem_conf, robot_id)
    individual = Individual(LGenotype)
    individuals.append(individual)
    robot_id += 1

#Do some new individual like in population next_gen()

new_individuals = []
for new_offsprings in range(offspring_size):
    # Selection operator (based on fitness)
    # Crossover
    if crossover_operator is not None:
        parents = multiple_selection(individuals,2,tournament_selection)
        child_genotype = Lcrossover(parents, lsystem_conf, crossover_conf)


    child_genotype._body_genome.id = robot_id
    robot_id += 1

    #mutation
    mutated_child = LMutation(child_genotype, mutation_conf)
















