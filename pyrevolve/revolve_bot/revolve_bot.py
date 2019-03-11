"""
Revolve body generator based on RoboGen framework
"""
import yaml
import math
from collections import OrderedDict

from pyrevolve.sdfbuilder import SDF
from pyrevolve.sdfbuilder import math as SDFmath
from pyrevolve.sdfbuilder import Model, Element, Link, FixedJoint
from pyrevolve.sdfbuilder.util import number_format

from .revolve_module import CoreModule
from .revolve_module import ActiveHingeModule
from .revolve_module import BrickModule
from .revolve_module import BrickSensorModule
from .revolve_module import Orientation
from .revolve_module import BoxSlot
from .brain_nn import BrainNN

import xml.etree.ElementTree


class RevolveBot:
    """
    Basic robot description class that contains robot's body and/or brain
    structures, ID and several other necessary parameters. Capable of reading
    a robot's sdf mode
    """

    def __init__(self, id=None):
        self._body = None
        self._brain = None
        self._id = id
        self._parents = None
        self._fitness = None
        self._behavioural_measurement = None
        self._battery_level = None

    def measure_behaviour(self):
        """

        :return:
        """
        pass

    def measure_body(self):
        """

        :return:
        """
        pass

    def measure_brain(self):
        """

        :return:
        """
        pass

    def load(self, text, conf_type):
        """
        Load robot's description from a string and parse it to Python structure
        :param text: Robot's description string
        :param conf_type: Type of a robot's description format
        :return:
        """
        if 'yaml' == conf_type:
            self.load_yaml(text)
        elif 'sdf' == conf_type:
            raise NotImplementedError("Loading from SDF not yet implemented")

    def load_yaml(self, text):
        """
        Load robot's description from a yaml string
        :param text: Robot's yaml description
        """
        yaml_bot = yaml.safe_load(text)
        self._id = yaml_bot['id'] if 'id' in yaml_bot else None
        self._body = CoreModule.FromYaml(yaml_bot['body'])

        if 'brain' in yaml_bot:
            yaml_brain = yaml_bot['brain']
            if 'type' not in yaml_brain:
                # raise IOError("brain type not defined, please fix it")
                brain_type = 'neural-network'
            else:
                brain_type = yaml_brain['type']

            if brain_type == 'neural-network':
                self._brain = BrainNN()
                self._brain.FromYaml(yaml_brain)

        else:
            self._brain = None

    def load_file(self, path, conf_type='yaml'):
        """
        Read robot's description from a file and parse it to Python structure
        :param path: Robot's description file path
        :param conf_type: Type of a robot's description format
        :return:
        """
        with open(path, 'r') as robot_file:
            robot = robot_file.read()

        self.load(robot, conf_type)

    def to_sdf(self, nice_format=None):
        return self._to_sdf_PYTHON_XML(nice_format)

    @staticmethod
    def _sdf_attach_module(module_slot, module_orientation: float,
                           visual, collision,
                           parent_slot, parent_collision):
        """
        Attaches `module` to `parent` using `parent_slot`.
        It modifies the pose of `visual` and `collision` to move them attached to the
        `parent_collision`
        :param module_slot:
        :param module_orientation: degrees of rotation of the component
        :param visual:
        :param collision:
        :param parent_slot:
        :param parent_collision:
        :return:
        """

        if module_orientation is not None:
            # Rotate the module_slot.tangent vector over the normal
            # with the given number of radians to apply
            # the rotation. Rotating this vector around
            # the normal should not break their orthogonality.
            orientation = module_orientation / 180.0 * math.pi
            rot = SDFmath.Quaternion.from_angle_axis(orientation, module_slot.normal)
            module_slot.tangent = rot * module_slot.tangent

        visual.align(
            module_slot,
            parent_slot,
            parent_collision,
            relative_to_child=True
        )
        collision.set_rotation(visual.get_rotation())
        old_translation = collision.get_position()
        collision.set_position(visual.get_position())
        collision.translate(collision.to_parent_direction(old_translation))

    def _module_to_sdf(self, module, parent_link, parent_slot: BoxSlot, parent_collision, slot_chain=''):
        from pyrevolve import SDF
        slot_chain = '{}{}'.format(slot_chain, parent_slot.orientation.short_repr())
        links = []

        my_link = parent_link
        my_collision = None

        if type(module) is ActiveHingeModule:
            print("adding joint")
            child_link = SDF.Link('{}_Leg'.format(slot_chain))
            links.append(child_link)

            visual_frame, collision_frame, \
            visual_servo, collision_servo, joint = module.to_sdf('{}_'.format(slot_chain))

            # parent_slot = Orientation(parent_slot)
            if parent_slot != Orientation.WEST:
                pass

            # parent_slot = parent_module.boxslot(parent_slot)
            module_slot = module.boxslot_frame(Orientation.SOUTH)
            self._sdf_attach_module(module_slot, module.orientation,
                                    visual_frame, collision_frame,
                                    parent_slot, parent_collision)

            parent_slot = module.boxslot_frame(Orientation.NORTH)
            module_slot = module.boxslot_servo(Orientation.SOUTH)
            self._sdf_attach_module(module_slot, None,
                                    visual_servo, collision_servo,
                                    parent_slot, collision_frame)

            parent_link.append(visual_frame)
            parent_link.append(collision_frame)

            child_link.append(visual_servo)
            child_link.append(collision_servo)

            my_link = child_link
            my_collision = collision_servo

        else:
            print("adding block")
            visual, collision = module.to_sdf('')

            module_slot = module.boxslot(Orientation.SOUTH)
            self._sdf_attach_module(module_slot, module.orientation,
                                    visual, collision,
                                    parent_slot, parent_collision)

            parent_link.append(visual)
            parent_link.append(collision)

            my_collision = collision

        # recursions on children
        for my_slot, child_module in module.iter_children():
            if child_module is None:
                continue

            my_slot = module.boxslot(Orientation(my_slot))
            children_links = self._module_to_sdf(child_module, my_link, my_slot, my_collision, slot_chain)
            links.extend(children_links)

        return links

    def _to_sdf_PYTHON_XML(self, nice_format):
        from xml.etree import ElementTree
        from pyrevolve import SDF

        sdf_root = ElementTree.Element('sdf', {'version': '1.6'})

        assert (self._id is not None)
        model = ElementTree.SubElement(sdf_root, 'model', {
            'name': str(self._id)
        })

        # TODO make this pose parametric
        pose = SDF.Pose(SDFmath.Vector3(0, 0, 0.05))
        model.append(pose)

        core_link = SDF.Link('Core')
        links = [core_link]
        core_visual, core_collision = self._body.to_sdf('')
        core_link.append(core_visual)
        core_link.append(core_collision)
        # core_link.append(inertial)

        parent_module = self._body
        parent_collision = core_collision

        for core_slot, child_module in self._body.iter_children():
            if child_module is None:
                continue
            core_slot = parent_module.boxslot(Orientation(core_slot))
            children_links = self._module_to_sdf(child_module, core_link, core_slot, core_collision)
            links.extend(children_links)

        for link in links:
            link.align_center_of_mass()
            link.calculate_inertial()
            model.append(link)

        # XML RENDER PHASE #
        def prettify(rough_string, indent='\t'):
            """Return a pretty-printed XML string for the Element.
            """
            import xml.dom.minidom
            reparsed = xml.dom.minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent=indent)

        # tree = xml.etree.ElementTree.ElementTree(sdf)
        res = xml.etree.ElementTree.tostring(sdf_root, encoding='utf8', method='xml')
        print(res)

        if nice_format is not None:
            res = prettify(res, nice_format)

        return res

    def _to_sdf_REVOLVE_XML(self):
        """
        Converts yaml to sdf

        :return:
        """
        sdf = SDF()

        model = Model(name=self._id)
        # TODO: Traverse through body elements, retrieve <link>s and
        # create <joint>s between them
        elements = [
            self._sdf_brain_plugin_conf()
        ]
        model.add_elements(elements)

        sdf.add_element(model)
        return sdf

    def _sdf_brain_plugin_conf(
            self,
            update_rate=5,
            controller_plugin='libRobotControlPlugin.so'
    ):
        """
        creates the plugin node with the brain configuration inside
        :param update_rate: Update rate as used by the default controller
        :type update_rate: float

        :param controller_plugin: Name of the shared
        library of the model plugin
        :type controller_plugin: str

        :return: The sdf model
        """
        plugin = Element(
            tag_name='plugin',
            attributes={
                'name': 'robot_controller',
                'filename': controller_plugin
            })

        config = Element(
            tag_name='rv:robot_config',
            attributes={
                'xmlns:rv': 'https://github.com/ci-group/revolve'
            })
        plugin.add_element(config)

        # update rate
        config.add_element(Element(
            tag_name='rv:update_rate',
            body=number_format(update_rate)))

        # brain
        if self._brain is not None:
            brain_config = self._brain.to_sdf()
            config.add_element(brain_config)

        # TODO sensors

        # TODO motors

        # battery
        if self._battery_level is not None:
            battery = Element(tag_name='rv:battery')
            battery_level = Element(
                tag_name='rv:level',
                body=self._battery_level
            )
            battery.add_element(battery_level)
            config.add_element(battery)

        return plugin

    def to_yaml(self):
        """
        Converts robot data structure to yaml

        :return:
        """
        yaml_dict = OrderedDict()
        yaml_dict['id'] = self._id
        yaml_dict['body'] = self._body.to_yaml()
        if self._brain is not None:
            yaml_dict['brain'] = self._brain.to_yaml()

        return yaml.dump(yaml_dict)

    def save_file(self, path, conf_type='yaml'):
        """
        Save robot's description on a given file path in a specified format
        :param path:
        :param conf_type:
        :return:
        """
        robot = ''
        if 'yaml' == conf_type:
            robot = self.to_yaml()
        elif 'sdf' == conf_type:
            robot = self.to_sdf()

        with open(path, 'w') as robot_file:
            robot_file.write(robot)

    def update_substrate(self):
        """
        Update all coordinates for body components

        :return:
        """
        return ''

    def render2d(self):
        """

        :return:
        """
        raise NotImplementedError("Render2D not yet implemented")
