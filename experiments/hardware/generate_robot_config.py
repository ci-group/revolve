"""
This script loads a robot.yaml file and creates the corresponding SDF and robot_config.yaml for the robot

This is useful to create the hardware configuration for the robot, starting from the yaml description of the robot.
"""

import os
import sys
import yaml
from collections import OrderedDict
import xml.etree.ElementTree

# Add `..` folder in search path
current_dir = os.path.dirname(os.path.abspath(__file__))
newpath = os.path.join(current_dir, '..', '..')
sys.path.append(newpath)

from pyrevolve import revolve_bot


async def run():
    # Load a robot from yaml
    robot = revolve_bot.RevolveBot()
    robot.load_file("experiments/examples/yaml/spider.yaml")
    robot.update_substrate()

    # Generate and Save the SDF file of the robot
    # robot.save_file('robot.sdf.xml', conf_type='sdf')
    robot_sdf = xml.etree.ElementTree.fromstring(robot.to_sdf())

    # Generate the robot_config.yaml
    ns = {'rv': 'https://github.com/ci-group/revolve'}

    sdf_model = robot_sdf.find('model')
    sdf_plugin = sdf_model.find('plugin')
    sdf_robot_config = sdf_plugin.find('rv:robot_config', ns)
    sdf_brain = sdf_robot_config.find('rv:brain', ns)
    sdf_actuators = sdf_brain.find('rv:actuators', ns)

    servos = []
    for actuator in sdf_actuators:
        coordinates = [float(v) for v in actuator.attrib['coordinates'].split(';')]
        servos.append({
            'pin': -1,
            'name': actuator.attrib['part_name'],
            'coordinates': coordinates,
            'inverse': False,
        })

    raspberry_yaml_conf = OrderedDict()
    raspberry_yaml_conf['robot_name'] = sdf_model.attrib['name']
    raspberry_yaml_conf['robot_id'] = 1
    raspberry_yaml_conf['robot_address'] = {
        # ip: "192.168.1.12"
        # port: 8888
    }
    raspberry_yaml_conf['servos'] = servos
    raspberry_yaml_conf['rgb_pins'] = [15, 14, 4]
    raspberry_yaml_conf['controller'] = {
        'type': "differential-cpg",
        # spider weights
        'weights': [],
    }

    with open('robot_conf.yaml', 'w') as robot_file:
        robot_file.write(yaml.dump(raspberry_yaml_conf))

    print('generated file "robot_conf.yaml", you still need to insert the correct pin numbers and check if some of the '
          'servos need to be Inverted')
