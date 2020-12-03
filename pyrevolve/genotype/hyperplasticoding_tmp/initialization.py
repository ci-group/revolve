from pyrevolve.genotype.hyperplasticoding_tmp.hyperplasticoding import HyperPlasticoding


def random_initialization(conf, next_robot_id):

    genotype = HyperPlasticoding(conf, next_robot_id)

    genotype.random_init()
    
    return genotype
