from __future__ import absolute_import
from math import radians
from sdfbuilder import Model, Element, Link, FixedJoint
from sdfbuilder.math import Quaternion, Vector3
from sdfbuilder.util import number_format as nf
from ...spec import Robot, BodyPart as PbBodyPart, BodyImplementation, NeuralNetImplementation
from ...spec.exception import err
from .neural_net import Neuron, NeuralConnection
from .body import Component, BodyPart
from .body.exception import ComponentException


class AspectBuilder(object):
    """
    Builder interface class, a subclass can be passed to the `RobotBuilder`
    as either a builder for a body or a builder for a brain.
    """

    def build(self, robot, model, plugin, analyzer_mode):
        """
        :param robot: Robot in whatever message type is applicable
        :param model:
        :type model: Model
        :param plugin:
        :type plugin: Element
        :param analyzer_mode:
        :type analyzer_mode: bool
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

    def build(self, robot, model, plugin, analyzer_mode):
        # First, align all the body parts and create the full graph
        connections, body_parts, components, motors = self._process_body_part(robot.body.root)

        if analyzer_mode:
            self._build_analyzer_body(model, body_parts, connections)
        else:
            # Assuming all components were correctly connected (which we
            # can check later on), we can now traverse the component tree
            # to build the body starting from any component
            traversed = set()
            self._build_body(traversed, model, plugin, components[0])

            diff = traversed.difference(components)
            if len(diff):
                diff_list = ", ".join(skipped.name for skipped in diff)
                raise ComponentException("The following components were defined but not traversed:\n%s\n"
                                         "Make sure all components are properly fixed or joined." % diff_list)

            # Sensors have been added in _build_body.
            # Adding motors should work just fine as-is since they render
            # the ID of the generated joint.
            plugin.add_elements(motors)

    def _build_analyzer_body(self, model, body_parts, connections):
        """
        Builds a model from body parts in analyzer mode - i.e.
        one link per body part to allow collision detection.
        :param model:
        :param body_parts:
        :type body_parts: list[BodyPart]
        :return:
        """
        part_map = {}
        for body_part in body_parts:
            link = Link("link_"+body_part.id, self_collide=True)
            link.set_position(body_part.get_position())
            link.set_rotation(body_part.get_rotation())
            body_part.set_position(Vector3())
            body_part.set_rotation(Quaternion())
            link.add_element(body_part)
            model.add_element(link)
            part_map[body_part.id] = link

        # Create fake joints for all connections so they will
        # not trigger collisions.
        for a, b in connections:
            joint = FixedJoint(part_map[a], part_map[b])
            model.add_element(joint)

    def _build_body(self, traversed, model, plugin, component, link=None, child_joints=None):
        """
        :param traversed: Set of components that were already traversed,
                          prevents loops (since all connections are two-sided).
        :type traversed: set
        :param model:
        :param plugin:
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
            # The position of the link is determined later when we decide
            # its center of mass.
            link = Link("link_%s" % component.name, self_collide=True)
            child_joints = []
            model.add_element(link)

        # Add this component to the link.
        position = link.to_local_frame(component.get_position())
        rotation = link.to_local_direction(component.get_rotation())
        component.set_position(position)
        component.set_rotation(rotation)
        link.add_element(component)

        # Add sensors registered on this component
        plugin.add_elements(component.get_plugin_sensors(link))

        for conn in component.connections:
            if conn.joint:
                # Create the subtree after the joint
                other_link = self._build_body(traversed, model, plugin, conn.other)
                if other_link is None:
                    # This connection was already created
                    # from the other side.
                    continue

                # Check whether this component is the parent or the child
                # of the joint connection (it is the parent by default)
                # This is relevant for another reason, because we will
                # be moving the internals of the current joint around
                # to center the inertia later on. This means that for
                # joints for which the current link is the child we need
                # to move the joint as well since the joint position is
                # expressed in the child frame. If the current link is
                # the parent there is no need to move it with this one,
                # and since `create_joint` is called after everything
                # within the child link has been fully neither does
                # the other link code.
                parent_link = link
                child_link = other_link
                is_child = conn.joint.parent is not component

                if is_child:
                    parent_link, child_link = other_link, link

                joint = conn.joint.create_joint(parent_link, child_link,
                                                conn.joint.parent, conn.joint.child)
                model.add_element(joint)

                if is_child:
                    child_joints.append(joint)
            else:
                # Just add this element to the current link
                self._build_body(traversed, model, plugin, conn.other, link, child_joints)

        if create_link:
            # Give the link the inertial properties of the combined collision,
            # only calculated by the item which created the link.
            # Note that we need to align the center of mass with the link's origin,
            # which will move the internal components around. In order to compensate
            # for this in the internal position we need to reposition the link according
            # to this change.
            translation = link.align_center_of_mass()
            link.translate(-translation)
            link.calculate_inertial()

            # Translate all the joints expressed in this link's frame that
            # were created before repositioning
            # Note that the joints need the same translation as the child elements
            # rather than the counter translation of the link.
            for joint in child_joints:
                joint.translate(translation)

        return link

    def _process_body_part(self, part, parent=None, src_slot=None, dst_slot=None):
        """
        Traverses and positions all body parts, creates connections between connected
        slots such that `_build_body` can later generate the actual robot body.

        :param part:
        :type part: PbBodyPart
        :return: List of body part components
        :rtype: tuple(list[BodyPart], list[Component], list[Motor])
        """
        spec = self.spec.get(part.type)
        if spec is None:
            err("Cannot build unknown part type '%s'." % part.type)

        body_part_class = spec.body_part
        kwargs = spec.unserialize_params(part.param)

        # Set the arity
        kwargs['arity'] = spec.arity
        body_part = body_part_class(part.id, self.conf, **kwargs)
        """ :type : BodyPart"""

        components = body_part.get_components()
        motors = body_part.get_motors()[:]
        body_parts = [body_part]
        connections = set()

        if parent:
            # Attach to parent
            body_part.attach(parent, src_slot, dst_slot, radians(part.orientation))
        else:
            # Just apply specified rotation around zero slot
            body_part.rotate_around(body_part.get_slot_normal(0), part.orientation, relative_to_child=True)

        # Process body connections
        for conn in part.child:
            connections.add((part.id, conn.part.id))
            cn, bp, cmp, mtr = self._process_body_part(conn.part, body_part, conn.src, conn.dst)
            components += cmp
            motors += mtr
            body_parts += bp
            connections.update(cn)

        return connections, body_parts, components, motors


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

    def build(self, robot, model, plugin, analyzer_mode):
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
        :type body_builder: AspectBuilder
        :param brain_builder:
        :type brain_builder: AspectBuilder
        """
        self.body_builder = body_builder
        self.brain_builder = brain_builder

    def get_sdf_model(self, robot, controller_plugin=None, update_rate=5, name="sdf_robot", analyzer_mode=False):
        """
        :param robot: Protobuf robot
        :type robot: Robot
        :param controller_plugin: Name of the shared library of the model plugin
        :type controller_plugin: str|none
        :param update_rate: Update rate as used by the default controller
        :type update_rate: float
        :param name: Name of the SDF model
        :type name: str
        :param analyzer_mode:
        :type analyzer_mode: bool
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

        self.brain_builder.build(robot, model, brain_config, analyzer_mode)
        self.body_builder.build(robot, model, config, analyzer_mode)

        if controller_plugin:
            # Only add the plugin element when required
            model.add_element(plugin)

        return model
