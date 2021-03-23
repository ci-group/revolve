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


class HyperPlasticoding(Genotype):

    def __init__(self, conf, robot_id):

        self.conf = conf
        self.id = str(robot_id)
        self.development_seed = None
        self.random = None
        self.quantity_modules = 1
        self.quantity_nodes = 0
        self.cppn = None
        # the queried substrate
        self.queried_substrate = {}
        self.phenotype = None
        self.parents_ids = []
        self.outputs_count = {
            'b_module':  0,
            'b2_module': 0,
            'a1_module': 0,
            'a2_module': 0 }
        self.environmental_conditions = {}

        self.cppn_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                       neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                       conf.cppn_config_path)

    def standard_output(self, value):
        # sigmoid
        value = 1.0 / (1.0 + math.exp(-value))
        return value

    def random_init(self):

        self.cppn = self.cppn_config.genome_type('')
        self.cppn.fitness = 0
        self.cppn.configure_new(self.cppn_config.genome_config)
        self.querying_seed = random.randint(1, 10000)

    def develop(self, environment):

        print('\n', environment)
         # Applyies regulation according to environmental conditions.
        if self.conf.plastic:

            # This check-block is a shortcut to save computational time,
            # but the imu sensors could for sure tell if the floor is inclined=1 or not_inclined=0.
            if environment == 'plane':
                self.environmental_conditions['inclined'] = 0
            if environment == 'tilted3':
                self.environmental_conditions['inclined'] = 1

        self.random = random.Random(self.querying_seed)

        self.quantity_modules = 1
        self.quantity_nodes = 0
        # the queried substrate
        self.queried_substrate = {}
        self.free_slots = {}
        self.outputs_count = {
            'b_module':  0,
            'b2_module': 0,
            'a1_module': 0,
            'a2_module': 0}

        self.phenotype = RevolveBot()
        self.phenotype._id = self.id if type(self.id) == str and self.id.startswith("robot") else "robot_{}".format(
            self.id)

        # size of substrate is (substrate_radius*2+1)^2
        cppn = neat.nn.FeedForwardNetwork.create(self.cppn, self.cppn_config)

        self.develop_body(cppn)
        self.develop_brain(cppn)

        logger.info('Robot ' + str(self.id) + ' was late-developed.')

        return self.phenotype

    def develop_body(self, cppn):

        self.place_head()
        self.attach_body(cppn)

    def develop_brain(self, cppn):
        self.phenotype._brain = BrainNN()

        self.query_outpt_params(cppn)

        self.add_imu_nodes()

    def query_outpt_params(self, cppn):
        for coordinates in self.queried_substrate:

            if self.queried_substrate[coordinates].info['module_type'] in (Alphabet.JOINT_VERTICAL, Alphabet.JOINT_HORIZONTAL):
                joint = self.queried_substrate[coordinates]

                # querying cpg params
                queried_params = self.query_brain_part(coordinates[0], coordinates[1],
                                                       cppn)
                self.quantity_nodes += 1

                node = Node()
                node.id = 'node' + str(self.quantity_nodes)
                node.part_id = joint.id
                node.layer = 'output'
                node.type = 'Oscillator'
                node.substrate_coordinates = coordinates

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

        return coordinates, turtle_direction
    
    def choose_free_slot(self):
        parent_module_coor = self.random.choice(list(self.free_slots.keys()))
        parent_module = self.queried_substrate[parent_module_coor]
        direction = self.random.choice(list(self.free_slots[parent_module_coor]))

        return parent_module_coor, parent_module, direction
        
    def attach_body(self, cppn):

        parent_module_coor = (0, 0)

        self.free_slots[parent_module_coor] = [Orientation.WEST.value,
                                              Orientation.NORTH.value,
                                              Orientation.EAST.value,
                                              Orientation.SOUTH.value]

        parent_module_coor, parent_module, direction = self.choose_free_slot()

        for q in range(0, self.conf.max_queries):

            # calculates coordinates of potential new module
            potential_module_coord, turtle_direction = self.calculate_coordinates(parent_module, direction)

            radius = self.conf.substrate_radius

            # substrate limit
            if radius >= potential_module_coord[0] >= -radius and radius >= potential_module_coord[1] >= -radius:

                # queries potential new module given coordinates
                module_type = \
                    self.query_body_part(potential_module_coord[0], potential_module_coord[1], cppn)

                # if position in substrate is not already occupied
                if potential_module_coord not in self.queried_substrate.keys():

                    new_module = self.new_module(module_type)

                    new_module.substrate_coordinates = potential_module_coord
                    new_module.orientation = \
                        self.get_angle(new_module.info['module_type'], parent_module)
                    new_module.info['turtle_direction'] = turtle_direction

                    self.quantity_modules += 1
                    new_module.id = str(self.quantity_modules)

                    # attaches module
                    parent_module.children[direction] = new_module
                    self.queried_substrate[potential_module_coord] = new_module

                    # joints branch out only to the front
                    if new_module.info['module_type'] in (
                    Alphabet.JOINT_VERTICAL, Alphabet.JOINT_HORIZONTAL):
                        directions = [Orientation.NORTH.value]
                    else:
                        directions = [Orientation.WEST.value,
                                      Orientation.NORTH.value,
                                      Orientation.EAST.value]

                    self.free_slots[parent_module_coor].remove(direction)
                    if len(self.free_slots[parent_module_coor]) == 0:
                        self.free_slots.pop(parent_module_coor)

                    # adds new slots fo list of free slots
                    self.free_slots[potential_module_coord] = directions

                    # fins new free slot
                    parent_module_coor, parent_module, direction = self.choose_free_slot()

                # use this for not stopping ofter finding an intersection for the first time
                # else:
                    #parent_module_coor = self.choose_free_slot()


    def place_head(self):

        module_type = Alphabet.CORE_COMPONENT
        module = CoreModule()
        module.id = str(self.quantity_modules)
        module.info = {'turtle_direction': Orientation.NORTH,
                       'module_type': module_type}
        module.orientation = 0
        module.rgb = self.get_color(module_type)

        self.phenotype._body = module
        self.queried_substrate[(0, 0)] = module

    def new_module(self, module_type):

        if module_type == Alphabet.BLOCK:
            module = BrickModule()
        if module_type == Alphabet.JOINT_VERTICAL \
                or module_type == Alphabet.JOINT_HORIZONTAL:
            module = ActiveHingeModule()

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

    def query_body_part(self, x_dest, y_dest, cppn):

        outputs = cppn.activate(( self.environmental_conditions['inclined'], x_dest, y_dest))
        which_module = {

            'b_module': outputs[0],
            'b2_module': outputs[1],
            'a1_module': outputs[2],
            'a2_module': outputs[3]
        }

        module_type = self.get_module_type(which_module)

        return module_type

    def query_brain_part(self, x_dest, y_dest, cppn):

        outputs = cppn.activate(( self.environmental_conditions['inclined'], x_dest, y_dest))
        params = {
            'period': outputs[4],
            'phase_offset': outputs[5],
            'amplitude': outputs[6]
        }

        return params

    def get_module_type(self, which_module):

        # choose neuron with highest value
        which_module = max(which_module.items(), key=operator.itemgetter(1))[0]

        self.outputs_count[which_module] += 1

        if which_module == 'a1_module':
            module_type = Alphabet.JOINT_HORIZONTAL
        elif which_module == 'a2_module':
            module_type = Alphabet.JOINT_VERTICAL
        elif which_module in ('b_module', 'b2_module'):
            module_type = Alphabet.BLOCK

        return module_type

    def get_color(self, module_type):

        rgb = []
        if module_type == Alphabet.BLOCK:
            rgb = [0, 0, 1]
        if module_type == Alphabet.JOINT_HORIZONTAL:
            rgb = [1, 0.08, 0.58]
        if module_type == Alphabet.JOINT_VERTICAL:
            rgb = [0.7, 0, 0]
        if module_type == Alphabet.CORE_COMPONENT:
            rgb = [1, 1, 0]

        return rgb

    def export_genotype(self, filepath):

        node_names = {-1: 'x_d',
                      -2: 'y_d',
                      0: 'b_module',
                      1: 'b2_module',
                      2: 'a1_module',
                      3: 'a2_module',
                      4: 'period',
                      5: 'phase_offset',
                      6: 'amplitude,'
                      }
        visualize.draw_net(self.cppn_config, self.cppn, False,
                           filepath + '/images/genotype_bodybrain_' + self.phenotype._id,
                           node_names=node_names)
        f = open(filepath + '/genotype_bodybrain_' + self.phenotype._id + '.txt', "w")
        f.write(str(self.cppn))
        f.close()

    def export_parents(self, filepath):

        filepath += '/genotypes_parents.txt'
        f = open(filepath, "a")
        line = self.phenotype._id + '\t'
        for parent in self.parents_ids:
            line += str(parent) + ' '

        f.write(line + '\n')
        f.close()

    def add_imu_nodes(self):
        for p in range(1, 7):
            id = 'node-core' + str(p)
            node = Node()
            node.layer = 'input'
            node.type = 'Input'
            node.part_id = self.phenotype._body.id
            node.id = id
            self.phenotype._brain.nodes[id] = node

class HyperPlasticodingConfig:
    def __init__(self,
                 robot_id=0,
                 plastic=False,
                 substrate_radius=14,
                 cppn_config_path='',
                 max_queries=14,
                 ):
        self.robot_id = robot_id
        self.plastic = plastic
        self.substrate_radius = substrate_radius
        self.cppn_config_path = cppn_config_path
        self.max_queries = max_queries



