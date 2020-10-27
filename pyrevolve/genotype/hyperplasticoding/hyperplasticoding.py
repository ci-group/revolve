import neat
import os


class HyperPlasticoding:
    
    def __init__(self, conf, robot_id):

        self.conf = conf
        self.id = str(robot_id)
        self.cppn_body = None

        local_dir = os.path.dirname(__file__)

        if not conf.plastic:
            body_config_path = os.path.join(local_dir, 'config-body-nonplastic')

        self.body_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                           neat.DefaultSpeciesSet, neat.DefaultStagnation,
                           body_config_path)

    def random_init(self):

        genome = self.body_config.genome_type(self.id)
        genome.fitness = 0
        genome.configure_new(self.body_config.genome_config)
        print('\n new genome:\n{!s}'.format(genome))
        self.cppn_body = genome


class HyperPlasticodingConfig:
    def __init__(self,
                 oscillator_param_min=1,
                 oscillator_param_max=10,
                 weight_param_min=-1,
                 weight_param_max=1,
                 weight_min=-1,
                 weight_max=1,
                 max_structural_modules=100,
                 robot_id=0,
                 plastic=False,
                 environmental_conditions=['hill'],
                 ):
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.weight_param_min = weight_param_min
        self.weight_param_max = weight_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.max_structural_modules = max_structural_modules
        self.robot_id = robot_id
        self.plastic = plastic
        self.environmental_conditions = environmental_conditions

