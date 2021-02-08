from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenomeConfig, DirectTreeGenome

if __name__ == "__main__":

    conf = DirectTreeGenomeConfig()

    genome1 = DirectTreeGenome(conf, 1)
    genome1.random_initialization()
    genome1.export_genotype("/tmp/test.yaml")
    robot1 = genome1.develop()

    # # create two robot genomes (direct + neat brain)
    # genome1 = DirectTreeNEATGenotype(genome_config, 2)
    # genome2 = DirectTreeNEATGenotype(genome_config, 3)
    #
    # print(genome1.id, genome1._body_genome.root, genome1._body_genome.root._nodes)
    # print(genome2.id, genome2._body_genome.root, genome2._body_genome.root._nodes)
    #
    # # genome mutation
    # mutation = Mutator(robogen_tree_generator)
    # genome3 = mutation.mutate(genome1, tree_mutation_neat_config, False)
    # genome4 = mutation.mutate(genome1, tree_mutation_neat_config, False)
    #
    # print(genome3.id, genome3._body_genome.root, genome3._body_genome.root._nodes)
    # print(genome4.id, genome4._body_genome.root, genome4._body_genome.root._nodes)
    #
    #
    # # crossover
    # tree_crossover = Crossover(robogen_tree_generator)
    # parents = [genome1, genome2]
    # genome5 = tree_crossover.crossover(parents, genome_config, tree_crossover_conf)
    #
    # print(genome5.id, genome5.root, genome5.root._nodes)
