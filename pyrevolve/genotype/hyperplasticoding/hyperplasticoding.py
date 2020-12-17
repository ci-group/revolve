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
        self.cppn = None
        # the queried substrate
        self.substrate = {}
        self.phenotype = None

        self.cppn_config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                       neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                       conf.cppn_config_path)

    def standard_output(self, value):
        # sigmoid
        value = 1.0 / (1.0 + math.exp(-value))
        return value

    def random_init(self, cppn):

        self.cppn = cppn
        self.cppn.fitness = 0

    def develop(self, environment):

        # simulates sensing of environmental conditions
        # if self.conf.plastic
        # ( it is a shortcut to save computational time,
        # but imu sensors could for sure tell if it is hill or not)
        # if environment == 'plane':
        #     hill = False
        # if environment == 'tilted5':
        #     hill = True

        radius = self.conf.substrate_radius

        self.phenotype = RevolveBot()
        self.phenotype._id = self.id if type(self.id) == str and self.id.startswith("robot") else "robot_{}".format(self.id)

        # size of substrate is (substrate_radius*2+1)^2
        cppn = neat.nn.FeedForwardNetwork.create(self.cppn, self.cppn_config)

        self.develop_body(radius, cppn)
        self.develop_brain(radius, cppn)

        logger.info('Robot ' + str(self.id) + ' was late-developed.')

        return self.phenotype

    def develop_body(self, radius, cppn):

        self.place_head()
        self.attach_body(self.phenotype._body, radius, cppn)

    def develop_brain(self, radius, cppn):
        self.phenotype._brain = BrainNN()

        self.query_outpt_params(radius, cppn)
        self.query_input_params(radius, cppn)
        # TODO: query inter cpg connections

        self.add_imu_nodes()

    def query_input_params(self, radius, cppn):

        for coordinates in self.substrate:

            if self.substrate[coordinates].info['module_type'] == Alphabet.SENSOR:

                self.quantity_nodes += 1
                node = Node()
                node.id = 'node' + str(self.quantity_nodes)
                node.part_id = self.substrate[coordinates].id
                node.layer = 'input'
                node.type = 'Input'
                node.substrate_coordinates = coordinates
                sensor = node

                self.phenotype._brain.nodes[node.id] = node

                for node in self.phenotype._brain.nodes:

                    if self.phenotype._brain.nodes[node].layer == 'output':
                        joint =  self.phenotype._brain.nodes[node]
                        queried_params = self.query_brain_part(sensor.substrate_coordinates[0], sensor.substrate_coordinates[1],
                                                               joint.substrate_coordinates[0], joint.substrate_coordinates[1],
                                                               radius, cppn)

                        # TODO: use a better threshold rule (later, try to guarantee there are no loose inputs)
                        if abs(queried_params['weight']) > 0.05:
                            connection = Connection()
                            connection.src = sensor.id
                            connection.dst = joint.id
                            connection.weight = queried_params['weight']
                            self.phenotype._brain.connections.append(connection)

    def query_outpt_params(self, radius, cppn):
        for coordinates in self.substrate:

            if self.substrate[coordinates].info['module_type'] in (Alphabet.JOINT_VERTICAL, Alphabet.JOINT_HORIZONTAL):
                joint = self.substrate[coordinates]

                # querying cpg params
                queried_params = self.query_brain_part(0, 0,
                                                       coordinates[0], coordinates[1],
                                                       radius, cppn)
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

                # querying output recurrence
                queried_params = self.query_brain_part(coordinates[0], coordinates[1],
                                                       coordinates[0], coordinates[1],
                                                       radius, cppn)
                # TODO: use a better threshold rule
                if abs(queried_params['weight']) > 0.05:
                    connection = Connection()
                    connection.src = node.id
                    connection.dst = node.id
                    connection.weight = queried_params['weight']
                    self.phenotype._brain.connections.append(connection)

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
        # maybe add it back in the future, BUT ONLY IF using a seed
        # random.shuffle(directions)

        # querying clockwise
        for direction in directions:

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

        # potential new modules crossing the boundaries of the substrate are not even queried
        if radius >= potential_module_coord[0] >= -radius and radius >= potential_module_coord[1] >= -radius:

            # queries potential new module given coordinates
            module_type = \
                self.query_body_part(0, 0, potential_module_coord[0], potential_module_coord[1], radius, cppn)

            # if cppn determines there is a module in the coordinate
            if module_type is not None:

                # if position in substrate is not already occupied
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
                        else:
                            new_module.id = parent_module.id + 's' + str(direction.value)

                        parent_module.children[direction.value] = new_module
                        self.substrate[potential_module_coord] = new_module

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

    def query_body_part(self, x_origin, y_origin, x_dest, y_dest, radius, cppn):

        x_origin_norm = self.normalize_value(x_origin, -radius, radius)
        y_origin_norm = self.normalize_value(y_origin, -radius, radius)
        x_dest_norm = self.normalize_value(x_dest, -radius, radius)
        y_dest_norm = self.normalize_value(y_dest, -radius, radius)

        d = self.calculate_d(x_dest_norm, y_dest_norm)

        outputs = cppn.activate((x_origin_norm, y_origin_norm, x_dest_norm, y_dest_norm, d))

        which_module = {
            'no_module': outputs[0],
            'b_module': outputs[1],
            'a1_module': outputs[2],
            'a2_module': outputs[3],
            't_module': outputs[4]
        }

        module_type = self.get_module_type(which_module)

        return module_type

    def query_brain_part(self, x_origin, y_origin, x_dest, y_dest, radius, cppn):

        x_origin_norm = self.normalize_value(x_origin, -radius, radius)
        y_origin_norm = self.normalize_value(y_origin, -radius, radius)
        x_dest_norm = self.normalize_value(x_dest, -radius, radius)
        y_dest_norm = self.normalize_value(y_dest, -radius, radius)

        d = self.calculate_d(x_dest_norm, y_dest_norm)

        outputs = cppn.activate((x_origin_norm, y_origin_norm, x_dest_norm, y_dest_norm, d))

        params = {
             'period': outputs[5],
             'phase_offset': outputs[6],
             'amplitude': outputs[7],
             'weight': neat.activations.clamped_activation(outputs[8])
        }

        return params

    def get_module_type(self, which_module):

        # choose neuron with highest value
        which_module = max(which_module.items(), key=operator.itemgetter(1))[0]
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

        node_names = {-1: 'x_o',
                      -2: 'y_o',
                      -3: 'x_d',
                      -4: 'y_d',
                      -5: 'd',
                      0: 'no_module',
                      1: 'b_module',
                      2: 'a1_module',
                      3: 'a2_module',
                      4: 't_module',
                      5: 'period',
                      6: 'phase_offset',
                      7: 'amplitude,',
                      8: 'weight'
                      }
        visualize.draw_net(self.cppn_config, self.cppn, False, filepath + '/images/genotype_bodybrain_' + self.phenotype._id,
                           node_names=node_names)
        f = open(filepath + '/genotype_bodybrain_' + self.phenotype._id + '.txt', "w")
        f.write(str(self.cppn))
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
                 robot_id=0,
                 plastic=False,
                 environmental_conditions=['hill'],
                 substrate_radius=4,
                 cppn_config_path=''
                 ):
        self.robot_id = robot_id
        self.plastic = plastic
        self.environmental_conditions = environmental_conditions
        self.substrate_radius = substrate_radius
        self.cppn_config_path = cppn_config_path


