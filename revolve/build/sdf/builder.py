from __future__ import absolute_import
from math import radians
from sdfbuilder import Model, Element, Link
from sdfbuilder.util import number_format as nf
from ...spec import Robot, BodyPart as PbBodyPart, BodyImplementation, NeuralNetImplementation
from ...spec.exception import err
from .neural_net import Neuron, NeuralConnection
from .body import Component
from .body.exception import ComponentException


class AspectBuilder(object):
    """
    Builder interface class, a subclass can be passed to the `RobotBuilder`
    as either a builder for a body or a builder for a brain.
    """

    def build(self, robot, model, plugin):
        """
        :param robot: Robot in whatever message type is applicable
        :param model:
        :type model: Model
        :param plugin:
        :type plugin: Element
        """
        raise NotImplementedError("Interface method.")


class BodyBuilder(AspectBuilder):
    """
    Default robot body builder. Assumes the example protobuf robot message,
    where a `robot.body.root` is present - any message that follows this
    convention will work as well.
    """

    def __init__(self, spec, conf=None):
        """
        :param spec:
        :type spec: BodyImplementation
        :param conf:
        :return:
        """
        self.conf = conf
        self.spec = spec

    def build(self, robot, model, plugin):
        # First, align all the body parts and create the full graph
        components = self._process_body_part(robot.body.root)
        # link = Link("only_link")
        # link.add_elements(components)
        # model.add_element(link)

        # Assuming all components were correctly connected (which we
        # can check later on), we can now traverse the component tree
        # to build the body starting from any component
        traversed = set()
        self._build_body(traversed, model, plugin, components[0])

        diff = traversed.difference(components)
        if len(diff):
            diff_list = ", ".join(skipped.name for skipped in diff)
            raise ComponentException("The following components were defined but not traversed:\n%s\n"
                                     "Make sure all components are propertly fixed or joined." % diff_list)

    def _build_body(self, traversed, model, plugin, component, link=None):
        """
        :param traversed: Set of components that were already traversed,
                          prevents loops may these be present.
        :type traversed: set
        :param component:
        :type component: Component
        :param link:
        :type link: Link
        :return: The primary link used in this traversal, i.e. the link
                 passed to it or the first link created.
        """
        if component in traversed:
            return link

        create_link = link is None
        traversed.add(component)
        if create_link:
            # New tree, create a link. The component name
            # should contain the body part ID so this name should
            # be unique.
            link = Link("link_%s" % component.name)

            # To have link poses make any sense, we give the link
            # the pose of the component that was first added to it.
            link.set_position(component.get_position())
            link.set_rotation(component.get_rotation())
            model.add_element(link)

        # Add this component to the link. Its position is in the global
        # frame, so we must use sibling frame conversion.
        position = link.to_local_frame(component.get_position())
        rotation = link.to_local_direction(component.get_rotation())
        component.set_position(position)
        component.set_rotation(rotation)
        link.add_element(component)

        for conn in component.connections:
            if conn.joint:
                # Create the subtree after the joint
                other_link = self._build_body(traversed, model, plugin, conn.other)
                if other_link is None:
                    # This connection was already created
                    # from the other side.
                    continue

                parent_link = link
                child_link = other_link

                if conn.joint.parent is not component:
                    parent_link, child_link = child_link, parent_link

                joint = conn.joint.create_joint(parent_link, child_link, conn.joint.parent, conn.joint.child)


                model.add_element(joint)
            else:
                # Just add this element to the current link
                self._build_body(traversed, model, plugin, conn.other, link)

        if create_link:
            # Give the link the inertial properties of the combined collision,
            # only calculated by the item which created the link.
            link.calculate_inertial()

        return link

    def _process_body_part(self, part, parent=None, src_slot=None, dst_slot=None):
        """
        :param part:
        :type part: PbBodyPart
        :return: List of body part components
        :rtype: list[Component]
        """
        spec = self.spec.get(part.type)
        if spec is None:
            err("Cannot build unknown part type '%s'." % part.type)

        body_part_class = spec.body_part
        kwargs = spec.unserialize_params(part.param)

        # Set the arity
        kwargs['arity'] = spec.arity
        body_part = body_part_class(part.id, self.conf, **kwargs)
        """:type : BodyPart"""

        components = body_part.get_components()

        if parent:
            # Attach to parent
            body_part.attach(parent, src_slot, dst_slot, radians(part.orientation))
        else:
            # Just apply specified rotation around zero slot
            body_part.rotate_around(body_part.get_slot_normal(0), part.orientation, relative_to_child=True)

        # Process body connections
        for conn in part.child:
            components += self._process_body_part(conn.part, body_part, conn.src, conn.dst)

        return components


class NeuralNetBuilder(AspectBuilder):
    """
    Default neural network builder. Assumes the neural net construction as specified
    in the example protobuf message.
    """

    def __init__(self, spec):
        """
        :param spec:
        :type spec: NeuralNetImplementation
        :return:
        """
        self.spec = spec

    def build(self, robot, model, plugin):
        self._process_brain(plugin, robot.brain)

    def _process_brain(self, plugin, brain):
        """
        :param plugin:
        :type plugin: Element
        :param brain:
        :return:
        """
        # Add neurons
        for neuron in brain.neuron:
            spec = self.spec.get(neuron.type)
            if spec is None:
                err("Cannot build unknown neuron type '%s'." % neuron.type)

            params = spec.unserialize_params(neuron.param)
            plugin.add_element(Neuron(neuron, params))

        # Add connections
        for conn in brain.connection:
            plugin.add_element(NeuralConnection(conn))


class RobotBuilder(object):
    """
    Creates a Robot builder which consists of something that builds a body
    and something that builds a brain.
    """

    def __init__(self, body_builder, brain_builder):
        """
        :param body_builder:
        :type body_builder: Builder
        :param brain_builder:
        :type brain_builder: Builder
        """
        self.body_builder = body_builder
        self.brain_builder = brain_builder

    def get_sdf_model(self, robot, controller_plugin=None, update_rate=5, name="sdf_robot"):
        """
        :param robot: Protobuf robot
        :type robot: Robot
        :param controller_plugin: Name of the shared library of the model plugin
        :type controller_plugin: str|none
        :param update_rate: Update rate as used by the default controller
        :type update_rate: float
        :param name: Name of the SDF model
        :type name: str
        :return: The sdfbuilder Model
        :rtype: Model
        """
        model = Model(name)

        # Create the model plugin element
        plugin = Element(tag_name='plugin', attributes={
            'name': 'robot_controller',
            'filename': controller_plugin
        })

        # Add body config element
        config = Element(tag_name='rv:robot_config', attributes={
            'xmlns:rv': 'https://github.com/ElteHupkes/revolve'
        })
        config.add_element(Element(tag_name='rv:update_rate', body=nf(update_rate)))
        plugin.add_element(config)

        # Add brain config element
        brain_config = Element(tag_name='rv:brain')
        config.add_element(brain_config)

        self.brain_builder.build(robot, model, brain_config)
        self.body_builder.build(robot, model, config)

        if controller_plugin:
            # Only add the plugin element if desired
            model.add_element(plugin)

        return model
