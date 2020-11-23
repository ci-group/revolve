from pyrevolve.genotype.hyperplasticoding.hyperplasticoding2 import HyperPlasticoding


def random_initialization(conf, next_robot_id):

    genotype = HyperPlasticoding(conf, next_robot_id)

    genotype.random_init()
    
    return genotype
