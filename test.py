#!/usr/bin/env python3

import pyrevolve.revolve_bot
import pyrevolve.genotype.plasticoding.plasticoding

if __name__ == "__main__":
    #robot = pyrevolve.revolve_bot.RevolveBot()
    # robot.load_file("/home/karinemiras/projects/revolve/models/robot_26.yaml")
    #robot.load_file("/home/karinemiras/projects/revolve/experiments/examples/yaml/robot_5.yaml")
    
    #robot.save_file("/tmp/test.yaml")

    conf = pyrevolve.genotype.plasticoding.plasticoding.PlasticodingConfig()

    # this parameter will be controlled later by the recovery process, recovered robots have their genotypes restored ('new'), istead of initialized ('old')
    gen = pyrevolve.genotype.plasticoding.plasticoding.Plasticoding(conf)
    new_genotype = 'new' #  this path will be defined appropriately later
    #gen.develop(new_genotype, 'experiments/karine_exps/genotype_5.txt')
    gen.develop(new_genotype)
