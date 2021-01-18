from pyrevolve.genotype.hyperplasticoding_neatspecies.hyperplasticoding import HyperPlasticoding


def random_initialization(conf, cppn, next_robot_id):

    genotype = HyperPlasticoding(conf, next_robot_id)

    genotype.random_init(cppn)
    
    return genotype
