from pyrevolve.genotype.direct_tree.direct_tree_config import DirectTreeGenotypeConfig
from pyrevolve.genotype.direct_tree.direct_tree_genotype import DirectTreeGenotype

if __name__ == "__main__":

    conf = DirectTreeGenotypeConfig(
        min_parts=1,
        mutation_p_delete_subtree=0,
        mutation_p_duplicate_subtree=0,
        mutation_p_swap_subtree=0,
        mutation_p_mutate_oscillators=1,
        mutation_p_mutate_oscillator=1,
    )

    genome1 = DirectTreeGenotype(conf, 1)
    genome1.random_initialization()
    genome1.export_genotype("/tmp/test.yaml")
    robot1 = genome1.develop()

    # TEST LOAD AND SAVE
    genome2 = DirectTreeGenotype(conf, 1)
    genome2.load_genotype("/tmp/test.yaml")
    genome2.export_genotype("/tmp/test2.yaml")

    g1_file = None
    g2_file = None
    with open('/tmp/test.yaml') as f:
        g1_file = f.read()
    with open('/tmp/test2.yaml') as f:
        g2_file = f.read()

    assert g1_file == g2_file

    # TEST MUTATION
    genome3 = genome1.clone()
    genome3 = genome3.mutate()
    genome3.export_genotype("/tmp/test3.yaml")

    # TEST CROSSOVER
    # genome2.crossover(genome1)

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
