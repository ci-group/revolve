from pyrevolve.revolve_bot import RevolveBot
from pyrevolve.revolve_bot.revolve_module import Orientation
from pyrevolve.revolve_bot.revolve_module import CoreModule
from pyrevolve.revolve_bot.revolve_module import ActiveHingeModule
from pyrevolve.revolve_bot.revolve_module import BrickModule
from pyrevolve.revolve_bot.revolve_module import TouchSensorModule
from pyrevolve.revolve_bot.brain.brain_nn import BrainNN
from pyrevolve.revolve_bot.brain.brain_nn import Node
from pyrevolve.revolve_bot.brain.brain_nn import Connection
from pyrevolve.revolve_bot.brain.brain_nn import Params
from enum import Enum
import math
import neat
import os
import random


class Alphabet(Enum):

    # Modules
    CORE_COMPONENT = 'C'
    JOINT_HORIZONTAL = 'AJ1'
    JOINT_VERTICAL = 'AJ2'
    BLOCK = 'B'
    SENSOR = 'ST'


class HyperPlasticoding:
    
    def __init__(self, conf, robot_id):

        self.conf = conf
        self.id = str(robot_id)
        self.quantity_modules = 1
        self.cppn_body = None
        self.cppn_brain = None
        self.substrate = {}
        self.phenotype = None

        local_dir = os.path.dirname(__file__)

        if not conf.plastic:
            body_config_path = os.path.join(local_dir, 'config-body-nonplastic')
            brain_config_path = os.path.join(local_dir, 'config-brain-nonplastic')
        
        else:
            body_config_path = os.path.join(local_dir, 'config-body-plastic')
            brain_config_path = os.path.join(local_dir, 'config-brain-plastic')

        self.body_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                           neat.DefaultSpeciesSet, neat.DefaultStagnation,
                           body_config_path)

        # self.brain_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
        #                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
        #                                brain_config_path)

    def standard_output(self, value):
        # sigmoid
        value = 1.0 / (1.0 + math.exp(-value))
        return value

    def random_init(self):

        self.cppn_body = self.body_config.genome_type('')
        self.cppn_body.fitness = 0
        self.cppn_body.configure_new(self.body_config.genome_config)
        
        print('\n new genome:\n{!s}'.format(self.cppn_body))

    def develop(self, environment):

        # simulates sensing of environmental conditions
        # ( it is a shortcut to save computational time,
        # but imu sensors could for sure tell if it is hill or not)
        # if environment == 'plane':
        #     hill = False
        # if environment == 'tilted5':
        #     hill = True

        self.phenotype = RevolveBot()
        self.phenotype._id = self.id if type(self.id) == str and self.id.startswith("robot") else "robot_{}".format(self.id)
        self.phenotype._brain = BrainNN()

        self.develop_body()

        return self.phenotype

    def develop_body(self):

        radius = int((self.conf.substrate_length-1)/2)
        cppn = neat.nn.FeedForwardNetwork.create(self.cppn_body, self.body_config)

        # for each column in the 2d space of the body
        for x in range(-radius, radius+1):
            # for each column row
            for y in range(-radius, radius+1):
                self.query_body(x, y, radius, cppn)

        print(self.substrate)
        print(self.phenotype)

    def place_head(self):

        module = CoreModule()
        module.id = str(self.quantity_modules)
        module.info = {'orientation': Orientation.NORTH,
                       'new_module_type': Alphabet.CORE_COMPONENT}
        module.orientation = 0
        module.rgb = [1, 1, 0]

        self.phenotype._body = module
        self.substrate[(0, 0)] = {'module_type': module,
                                  'parent_slot': None}

    def place_module(self, module_type):

        if module_type == Alphabet.BLOCK:
            module = BrickModule()
        if module_type == Alphabet.JOINT_VERTICAL \
                or module_type == Alphabet.JOINT_HORIZONTAL:
            module = ActiveHingeModule()
        if module_type == Alphabet.SENSOR:
            module = TouchSensorModule()

        module.info = {}
        module.info['new_module_type'] = module_type
        # module.orientation = self.get_angle(module_type,
        #                                         self.mounting_reference)
        module.rgb = self.get_color(module_type)
        if module_type != Alphabet.SENSOR:
            self.quantity_modules += 1
            module.id = str(self.quantity_modules)

    def get_angle(self, module_type, parent):
        angle = 0
        if module_type == Alphabet.JOINT_VERTICAL:
            if parent.info['new_module_type'] is Alphabet.JOINT_VERTICAL:
                angle = 0
            else:
                angle = 90
        else:
            if parent.info['new_module_type'] is Alphabet.JOINT_VERTICAL:
                angle = 270
        return angle

    def query_body(self, x, y, radius, cppn):

        x_norm = self.normalize_value(x, -radius, radius)
        y_norm = self.normalize_value(y, -radius, radius)

        if x_norm == 0.5 and y_norm == 0.5:
            self.place_head()
        else:
            d = self.calculate_d(x_norm, y_norm)

            # print('\n',x_norm, y_norm, d)

            outputs = cppn.activate((x_norm, y_norm, d))
            # print(outputs)
            outputs = [self.standard_output(item) for item in outputs]
            # print(outputs)

            is_module = self.get_is_module(outputs[0])
            module_type = self.get_module_type(outputs[1])
            parent_slot = self.get_parent_slot(outputs[2])

            # ini temporary test!
            is_module = self.get_is_module(random.uniform(0, 1))
            module_type = self.get_module_type(random.uniform(0, 1))
            parent_slot = self.get_parent_slot(random.uniform(0, 1))
            # end temporary test!

            print(is_module, module_type, parent_slot)

    def get_is_module(self, output):
        is_module = True if output > 0.5 else False
        return is_module

    def get_module_type(self, output):

        if 0 <= output < 0.25:
            module_type = Alphabet.JOINT_HORIZONTAL
        elif 0.25 <= output < 0.5:
            module_type = Alphabet.JOINT_VERTICAL
        elif 0.5 <= output < 0.75:
            module_type = Alphabet.BLOCK
        elif 0.75 <= output <= 1:
            module_type = Alphabet.SENSOR

        return module_type

    def get_parent_slot(self, output):

        if 0 <= output < 0.25:
            parent_slot = Orientation.SOUTH
        elif 0.25 <= output < 0.5:
            parent_slot = Orientation.WEST
        elif 0.5 <= output < 0.75:
            parent_slot = Orientation.NORTH
        elif 0.75 <= output <= 1:
            parent_slot = Orientation.EAST

        return parent_slot

    def get_color(self, new_module_type):

        rgb = []
        if new_module_type == Alphabet.BLOCK:
            rgb = [0, 0, 1]
        if new_module_type == Alphabet.JOINT_HORIZONTAL:
            rgb = [1, 0.08, 0.58]
        if new_module_type == Alphabet.JOINT_VERTICAL:
            rgb = [0.7, 0, 0]
        if new_module_type == Alphabet.SENSOR:
            rgb = [0.7, 0.7, 0.7]
        return rgb

    def normalize_value(self, value, min, max):
        normalized_value = (value - min) / (max - min)
        return normalized_value

    def calculate_d(self, x_norm, y_norm):
        center = 0.5
        d = abs(x_norm - center) + abs(y_norm - center)
        return d


class HyperPlasticodingConfig:
    def __init__(self,
                 oscillator_param_min=1,
                 oscillator_param_max=10,
                 weight_min=-1,
                 weight_max=1,
                 robot_id=0,
                 plastic=False,
                 environmental_conditions=['hill'],
                 substrate_length=3#9
                 ):
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.robot_id = robot_id
        self.plastic = plastic
        self.environmental_conditions = environmental_conditions
        self.substrate_length = substrate_length

