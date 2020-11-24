from enum import Enum
from pyrevolve.genotype import Genotype
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
from ...custom_logging.logger import logger
import math
import neat
import os
import random
import operator
from pyrevolve.genotype.hyperplasticoding import visualize
import sys


class Alphabet(Enum):

    # Modules
    CORE_COMPONENT = 'C'
    JOINT_HORIZONTAL = 'AJ1'
    JOINT_VERTICAL = 'AJ2'
    BLOCK = 'B'
    SENSOR = 'ST'


class HyperPlasticoding(Genotype):
    
    def __init__(self, conf, robot_id):

        self.conf = conf
        self.id = str(robot_id)
        self.quantity_modules = 1
        self.quantity_nodes = 0
        self.cppn_body = None
        self.cppn_brain = None
        # the queried substrate
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

        self.brain_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                        neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                        brain_config_path)

    def standard_output(self, value):
        # sigmoid
        value = 1.0 / (1.0 + math.exp(-value))
        return value

    def random_init(self):

        self.cppn_body = self.body_config.genome_type('')
        self.cppn_body.fitness = 0
        self.cppn_body.configure_new(self.body_config.genome_config)

        self.cppn_brain = self.brain_config.genome_type('')
        self.cppn_brain.fitness = 0
        self.cppn_brain.configure_new(self.brain_config.genome_config)
        
        print('\n new genome body:\n{!s}'.format(self.cppn_body))
        print('\n new genome brain:\n{!s}'.format(self.cppn_brain))

    def develop(self, environment):

        # simulates sensing of environmental conditions
        # ( it is a shortcut to save computational time,
        # but imu sensors could for sure tell if it is hill or not)
        # if environment == 'plane':
        #     hill = False
        # if environment == 'tilted5':
        #     hill = True

        radius = self.conf.substrate_radius

        self.phenotype = RevolveBot()
        self.phenotype._id = self.id if type(self.id) == str and self.id.startswith("robot") else "robot_{}".format(self.id)

        self.develop_body(radius)
        self.develop_brain(radius)

        logger.info('Robot ' + str(self.id) + ' was late-developed.')

        return self.phenotype

    def develop_body(self, radius):

        # size of substrate is (substrate_radius*2+1)^2
        cppn_body = neat.nn.FeedForwardNetwork.create(self.cppn_body, self.body_config)

        self.place_head()
        self.attach_body(self.phenotype._body, radius, cppn_body)

    def develop_brain(self, radius):
        print('brainnnnn')
        self.phenotype._brain = BrainNN()
        cppn_brain = neat.nn.FeedForwardNetwork.create(self.cppn_brain, self.brain_config)

        self.query_cpg_params(radius, cppn_brain)

        self.add_imu_nodes()

    def query_cpg_params(self, radius, cppn_brain):
        for coordinates in self.substrate:

            if self.substrate[coordinates].info['module_type'] in (Alphabet.JOINT_VERTICAL, Alphabet.JOINT_HORIZONTAL):
                joint = self.substrate[coordinates]
                queried_params = self.query_brain_part(coordinates[0], coordinates[1], radius, cppn_brain)
                print('queried_params',queried_params)
                self.quantity_nodes += 1

                node = Node()
                node.id = 'node' + str(self.quantity_nodes)
                node.part_id = joint.id
                node.layer = 'output'
                node.type = 'Oscillator'

                params = Params()
                params.period = queried_params['period']
                params.phase_offset = queried_params['phase_offset']
                params.amplitude = queried_params['amplitude']

                node.params = params

                self.phenotype._brain.params[node.id] = params
                self.phenotype._brain.nodes[node.id] = node

    def calculate_coordinates(self, parent, slot):

        # calculate the actual 2d direction and coordinates of new module using relative-to-parent position as reference

        dic = {Orientation.NORTH.value: 0,
               Orientation.WEST.value: 1,
               Orientation.SOUTH.value: 2,
               Orientation.EAST.value: 3}

        inverse_dic = {0: Orientation.NORTH.value,
                       1: Orientation.WEST.value,
                       2: Orientation.SOUTH.value,
                       3: Orientation.EAST.value}

        direction = dic[parent.info['turtle_direction'].value] + dic[slot]
        if direction >= len(dic):
            direction = direction - len(dic)

        turtle_direction = Orientation(inverse_dic[direction])
        if turtle_direction == Orientation.WEST:
            coordinates = (parent.substrate_coordinates[0] - 1,
                           parent.substrate_coordinates[1])
        if turtle_direction == Orientation.EAST:
            coordinates = (parent.substrate_coordinates[0] + 1,
                           parent.substrate_coordinates[1])
        if turtle_direction == Orientation.NORTH:
            coordinates = (parent.substrate_coordinates[0],
                           parent.substrate_coordinates[1] + 1)
        if turtle_direction == Orientation.SOUTH:
            coordinates = (parent.substrate_coordinates[0],
                           parent.substrate_coordinates[1] - 1)
        print(coordinates, turtle_direction)
        return coordinates, turtle_direction

    def attach_body(self, parent_module, radius, cppn):

        # core component is the only module that can grow to the back, because it has no parent
        if parent_module.info['module_type'] == Alphabet.CORE_COMPONENT:
            directions = [Orientation.WEST.value,
                          Orientation.NORTH.value,
                          Orientation.EAST.value,
                          Orientation.SOUTH.value]
        # joints branch out only to the front
        elif parent_module.info['module_type'] in (Alphabet.JOINT_VERTICAL, Alphabet.JOINT_HORIZONTAL):
            directions = [Orientation.NORTH.value]
        else:
            directions = [Orientation.WEST.value,
                          Orientation.NORTH.value,
                          Orientation.EAST.value]

        # order of children-querying is random
        random.shuffle(directions)

        print('\n')

        for direction in directions:
            print('\n  parent_module.coord', parent_module.substrate_coordinates,'direction', direction)

            # queries and (possibly) attaches surroundings modules to module
            self.attach_module(parent_module, Orientation(direction), radius, cppn)

            # if managed to attach a potential module, tried to branch out recursively
            if parent_module.children[direction] is not None:
                # sensors are terminals and thus do not branch out
                if parent_module.children[direction].info['module_type'] != Alphabet.SENSOR:
                    self.attach_body(parent_module.children[direction], radius, cppn)

    def attach_module(self, parent_module, direction, radius, cppn):

        # calculates coordinates of potential new module
        potential_module_coord, turtle_direction = self.calculate_coordinates(parent_module, direction.value)

        print('potential_module_coord', potential_module_coord)

        # potential new modules crossing the boundaries of the substrate are not even queried
        if radius >= potential_module_coord[0] >= -radius and radius >= potential_module_coord[1] >= -radius:

            # queries potential new module given coordinates
            module_type = \
                self.query_body_part(potential_module_coord[0], potential_module_coord[1], radius, cppn)

            # if cppn determines there is a module in the coordinate
            if module_type is not None:

                # move if up later
                if potential_module_coord not in self.substrate.keys():
                    valid_attachment = True

                    # sensors can not be attached to joints
                    # TODO: maybe allow that in the future?
                    if parent_module.info['module_type'] in (Alphabet.JOINT_VERTICAL, Alphabet.JOINT_HORIZONTAL) \
                            and module_type == Alphabet.SENSOR:
                        valid_attachment = False

                    # if attachment constraints are met
                    if valid_attachment:
                        new_module = self.new_module(module_type)
                        new_module.substrate_coordinates = potential_module_coord
                        new_module.orientation = \
                            self.get_angle(new_module.info['module_type'], parent_module)
                        new_module.info['turtle_direction'] = turtle_direction

                        if new_module.info['module_type'] != Alphabet.SENSOR:
                            self.quantity_modules += 1
                            new_module.id = str(self.quantity_modules)

                        parent_module.children[direction.value] = new_module
                        self.substrate[potential_module_coord] = new_module
                        print('\n##ADD!\n')
                    else:
                        print('invalid')

    def place_head(self):

        module_type = Alphabet.CORE_COMPONENT
        module = CoreModule()
        module.id = str(self.quantity_modules)
        module.info = {'turtle_direction': Orientation.NORTH,
                       'module_type': module_type}
        module.orientation = 0
        module.rgb = self.get_color(module_type)

        self.phenotype._body = module
        # TODO: experiment with evolvable position for the head
        self.substrate[(0, 0)] = module

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
        # print('\n',x_norm, y_norm, d),

        outputs = cppn.activate((x_norm, y_norm, d))
        print(outputs)

        which_module = {
            'no_module': outputs[0],
            'b_module': outputs[1],
            'a1_module': outputs[2],
            'a2_module': outputs[3],
            't_module': outputs[4]
        }

        module_type = self.get_module_type(which_module)

        print('module_type',module_type)

        return module_type

    def query_brain_part(self, x, y, radius, cppn):

        x_norm = self.normalize_value(x, -radius, radius)
        y_norm = self.normalize_value(y, -radius, radius)

        d = self.calculate_d(x_norm, y_norm)
        # print('\n',x_norm, y_norm, d),

        outputs = cppn.activate((x_norm, y_norm, d))

        params = {
            'period': outputs[0],
            'phase_offset': outputs[1],
            'amplitude': outputs[2],
            'weight': outputs[3]
        }

        #TODO: apply transformations to outputs

        return params

    def get_module_type(self, which_module):

        which_module = max(which_module.items(), key=operator.itemgetter(1))[0]
        print(which_module)
        if which_module == 'a1_module':
            module_type = Alphabet.JOINT_HORIZONTAL
        elif which_module == 'a2_module':
            module_type = Alphabet.JOINT_VERTICAL
        elif which_module == 'b_module':
            module_type = Alphabet.BLOCK
        elif which_module == 't_module':
            module_type = Alphabet.SENSOR
        else:
            module_type = None

        return module_type

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

        node_names = {-1: 'x',
                      -2: 'y',
                      -3: 'd',
                      0: 'no_module',
                      1: 'b_module',
                      2: 'a1_module',
                      3: 'a2_module',
                      4: 't_module'}
        visualize.draw_net(self.body_config, self.cppn_body, False, filepath + '/images/genotype_body_' + self.phenotype._id,
                           node_names=node_names)
        f = open(filepath + '/genotype_body_' + self.phenotype._id + '.txt', "w")
        f.write(str(self.cppn_body))
        f.close()

        node_names = {-1: 'x',
                      -2: 'y',
                      -3: 'd',
                      0: 'period',
                      1: 'phase_offset',
                      2: 'amplitude,',
                      3: 'weight'}
        visualize.draw_net(self.brain_config, self.cppn_brain, False, filepath + '/images/genotype_brain_' + self.phenotype._id,
                           node_names=node_names)
        f = open(filepath + '/genotype_brain_' + self.phenotype._id + '.txt', "w")
        f.write(str(self.cppn_brain))
        f.close()

    def add_imu_nodes(self):
        for p in range(1, 7):
            id = 'node-core'+str(p)
            node = Node()
            node.layer = 'input'
            node.type = 'Input'
            node.part_id = self.phenotype._body.id
            node.id = id
            self.phenotype._brain.nodes[id] = node


class HyperPlasticodingConfig:
    def __init__(self,
                 oscillator_param_min=1,
                 oscillator_param_max=10,
                 weight_min=-1,
                 weight_max=1,
                 robot_id=0,
                 plastic=False,
                 environmental_conditions=['hill'],
                 substrate_radius=4
                 ):
        self.oscillator_param_min = oscillator_param_min
        self.oscillator_param_max = oscillator_param_max
        self.weight_min = weight_min
        self.weight_max = weight_max
        self.robot_id = robot_id
        self.plastic = plastic
        self.environmental_conditions = environmental_conditions
        self.substrate_radius = substrate_radius
        self.is_hyper = True

