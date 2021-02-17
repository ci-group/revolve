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
    genome2 = DirectTreeGenotype(conf, 2)
    genome2.random_initialization()
    genome2.export_genotype("/tmp/test.yaml")

    genome4 = genome1.crossover(genome2, 4)
    genome4.export_genotype("/tmp/test4.yaml")
