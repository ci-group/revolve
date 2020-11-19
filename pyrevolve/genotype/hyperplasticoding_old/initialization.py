from pyrevolve.genotype.hyperplasticoding_old.hyperplasticoding import HyperPlasticoding


def random_initialization(conf, next_robot_id):

    genotype = HyperPlasticoding(conf, next_robot_id)

    genotype.random_init()
    
    return genotype
