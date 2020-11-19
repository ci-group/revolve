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
import pprint
from matplotlib.pyplot import figure
from matplotlib.ticker import MaxNLocator


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

        # size of substrate is (substrate_radius*2+1)^2
        radius = self.conf.substrate_radius
        body_cppn = neat.nn.FeedForwardNetwork.create(self.cppn_body, self.body_config)

        # self.query_body(radius, body_cppn)
        # self.attach_body()

        self.place_head()
        self.query_attach_body(self.phenotype._body, radius, body_cppn)

    def query_attach_body(self, module, radius, cppn):

        module.substrate_coordinates

        west = tuple(map(sum, zip(point, (-1, 0))))
        north = tuple(map(sum, zip(point, (0, 1))))
        east = tuple(map(sum, zip(point, (1, 0))))
        south = tuple(map(sum, zip(point, (0, -1))))

        print(west, north, east, south)

        # if self.substrate[point]['parent_direction'] == Orientation.NORTH:
        #     parent_point = tuple(map(sum, zip(point, (0, 1))))
        #
        # elif self.substrate[point]['parent_direction'] == Orientation.SOUTH:
        #     parent_point = tuple(map(sum, zip(point, (0, -1))))
        #
        # elif self.substrate[point]['parent_direction'] == Orientation.WEST:
        #     parent_point = tuple(map(sum, zip(point, (-1, 0))))
        #
        # elif self.substrate[point]['parent_direction'] == Orientation.EAST:
        #     parent_point = tuple(map(sum, zip(point, (1, 0))))

        #self.query_body_part(x, y, radius, cppn)

    def query_body(self, radius, cppn):

        # for each column in the 2d space (left to right)
        for x in range(-radius, radius + 1):
            # for each row of the column (bottom to top)
            for y in range(-radius, radius + 1):
                print(x, y)
                self.query_body_part(x, y, radius, cppn)

        self.draw_queried_substrate()

    def attach_body(self):

        for point in self.substrate:
            valid_attachment = True

            # head has no parent
            if point == (0, 0):
                valid_attachment = False
            else:

                if self.substrate[point]['parent_direction'] == Orientation.NORTH:
                    parent_point = tuple(map(sum, zip(point, (0, 1))))
                    parent_slot = Orientation.SOUTH

                elif self.substrate[point]['parent_direction'] == Orientation.SOUTH:
                    parent_point = tuple(map(sum, zip(point, (0, -1))))
                    parent_slot = Orientation.NORTH

                elif self.substrate[point]['parent_direction'] == Orientation.WEST:
                    parent_point = tuple(map(sum, zip(point, (-1, 0))))
                    parent_slot = Orientation.EAST

                elif self.substrate[point]['parent_direction'] == Orientation.EAST:
                    parent_point = tuple(map(sum, zip(point, (1, 0))))
                    parent_slot = Orientation.WEST

                # coordinates candidate to parent are empty or out of substrate
                if parent_point not in self.substrate.keys():
                    valid_attachment = False
                else:
                    # sensors are terminals and thus can not be parents
                    if self.substrate[parent_point]['module'].info['module_type'] == Alphabet.SENSOR:
                        valid_attachment = False

                    # joints do not connect to sensors
                    # TODO: allow that in the future?
                    elif self.substrate[parent_point]['module'].info['module_type'] \
                            in (Alphabet.JOINT_VERTICAL, Alphabet.JOINT_HORIZONTAL) \
                            and self.substrate[point]['module'].info['module_type'] == Alphabet.SENSOR:
                        valid_attachment = False

            # attaching module to due parent slot
            if valid_attachment:

                self.substrate[parent_point]['module'].children[parent_slot.value] = self.substrate[point]['module']

                self.substrate[point]['module'].orientation =\
                    self.get_angle(self.substrate[point]['module'].info['module_type'],
                                   self.substrate[parent_point]['module'])

                if self.substrate[point]['module'].info['module_type'] != Alphabet.SENSOR:
                    # TODO: check if it is skipping some cases
                    self.quantity_modules += 1
                    self.substrate[point]['module'].id = str(self.quantity_modules)

    def draw_queried_substrate(self):

        x = []
        y = []
        markers = []
        color = []
        for point in self.substrate:
            print(point,self.substrate[point]['parent_direction'])
            x.append(point[0])
            y.append(point[1])

            if self.substrate[point]['parent_direction'] == Orientation.SOUTH:
                markers.append('v')
            elif self.substrate[point]['parent_direction'] == Orientation.NORTH:
                markers.append('^')
            elif self.substrate[point]['parent_direction'] == Orientation.WEST:
                markers.append('<')
            elif self.substrate[point]['parent_direction'] == Orientation.EAST:
                markers.append('>')
            else:
                markers.append('o')

            color.append(tuple(self.get_color(self.substrate[point]['module'].info['module_type'])))

        ax = figure().gca()
        for xp, yp, m, c in zip(x, y, markers, color):
            ax.scatter([xp], [yp], marker=m, color=c, s=400)
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.get_figure().savefig('tmp.png')

    def place_head(self):

        module_type = Alphabet.CORE_COMPONENT
        module = CoreModule()
        module.id = str(self.quantity_modules)
        module.info = {'orientation': Orientation.NORTH,
                       'module_type': module_type}
        module.orientation = 0
        module.rgb = self.get_color(module_type)

        self.phenotype._body = module
        # TODO: experiment with evolvable position for the head
        self.substrate[(0, 0)] = {'module': module,
                                  'parent_direction': None}

    def new_module(self, module_type):

        if module_type == Alphabet.BLOCK:
            module = BrickModule()
        if module_type == Alphabet.JOINT_VERTICAL \
                or module_type == Alphabet.JOINT_HORIZONTAL:
            module = ActiveHingeModule()
        if module_type == Alphabet.SENSOR:
            module = TouchSensorModule()

        module.info = {}
        module.info['module_type'] = module_type
        module.rgb = self.get_color(module_type)

        return module

    def get_angle(self, module_type, parent):
        angle = 0
        if module_type == Alphabet.JOINT_VERTICAL:
            if parent.info['module_type'] is Alphabet.JOINT_VERTICAL:
                angle = 0
            else:
                angle = 90
        else:
            if parent.info['module_type'] is Alphabet.JOINT_VERTICAL:
                angle = 270
        return angle

    def query_body_part(self, x, y, radius, cppn):

        x_norm = self.normalize_value(x, -radius, radius)
        y_norm = self.normalize_value(y, -radius, radius)

        d = self.calculate_d(x_norm, y_norm)
        # print('\n',x_norm, y_norm, d)

        outputs = cppn.activate((x_norm, y_norm, d))
        # print(outputs)
        outputs = [self.standard_output(item) for item in outputs]
        # print(outputs)

        is_module = self.get_is_module(outputs[0])
        module_type = self.get_module_type(outputs[1])
        parent_direction = self.get_parent_direction(outputs[2])

        # ini temporary test!
        is_module = True#self.get_is_module(random.uniform(0, 1))
        module_type = self.get_module_type(random.uniform(0, 1))
        parent_direction = Orientation.WEST#self.get_parent_direction(random.uniform(0, 1))
        # end temporary test!

        print('is_module ', is_module, 'module_type ', module_type, 'parent_direction ', parent_direction)

        return is_module, self.new_module(module_type), parent_direction

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

    def get_parent_direction(self, output):

        if 0 <= output < 0.25:
            parent_direction = Orientation.SOUTH
        elif 0.25 <= output < 0.5:
            parent_direction = Orientation.WEST
        elif 0.5 <= output < 0.75:
            parent_direction = Orientation.NORTH
        elif 0.75 <= output <= 1:
            parent_direction = Orientation.EAST

        return parent_direction

    def get_color(self, module_type):

        rgb = []
        if module_type == Alphabet.BLOCK:
            rgb = [0, 0, 1]
        if module_type == Alphabet.JOINT_HORIZONTAL:
            rgb = [1, 0.08, 0.58]
        if module_type == Alphabet.JOINT_VERTICAL:
            rgb = [0.7, 0, 0]
        if module_type == Alphabet.SENSOR:
            rgb = [0.7, 0.7, 0.7]
        if module_type == Alphabet.CORE_COMPONENT:
            rgb = [1, 1, 0]

        return rgb

    def normalize_value(self, value, min, max):
        normalized_value = (value - min) / (max - min)
        return normalized_value

    def calculate_d(self, x_norm, y_norm):
        center = 0.5
        d = abs(x_norm - center) + abs(y_norm - center)
        return d

    def export_genotype(self, filepath):
        # TODO: export cppn
        pass


class HyperPlasticodingConfig:
    def __init__(self,
                 oscillator_param_min=1,
                 oscillator_param_max=10,
                 weight_min=-1,
                 weight_max=1,
                 robot_id=0,
                 plastic=False,
                 environmental_conditions=['hill'],
                 substrate_radius=2#1
                 ):
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.robot_id = robot_id
        self.plastic = plastic
        self.environmental_conditions = environmental_conditions
        self.substrate_radius = substrate_radius

