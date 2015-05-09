from math import radians
from sdfbuilder import Model, Element
from ...spec import Robot, BodyPart as PbBodyPart, BodyImplementation, NeuralNetImplementation
from ...spec.exception import err
from neural_net import Neuron, NeuralConnection


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
        self._process_body_part(model, robot.body.root, plugin)

    def _process_body_part(self, model, part, plugin, parent=None, src_slot=None, dst_slot=None):
        """
        :param model:
        :type model: Model
        :param part:
        :type part: PbBodyPart
        :param plugin:
        :type plugin: Element
        :return:
        """
        spec = self.spec.get(part.type)
        if spec is None:
            err("Cannot build unknown part type '%s'." % part.type)

        body_part = spec.body_part
        kwargs = spec.unserialize_params(part.param)

        # Set the arity
        kwargs['arity'] = spec.arity
        sdf_part = body_part(part.id, self.conf, **kwargs)
        """:type : BodyPart"""

        if parent:
            # Attach to parent
            sdf_part.attach(parent, src_slot, dst_slot, radians(part.orientation))

        model.add_element(sdf_part)
        model.add_elements(sdf_part.joints)

        # Add sensors and motors
        plugin.add_elements(sdf_part.get_sensors())
        plugin.add_elements(sdf_part.get_motors())

        # Process body connections
        for conn in part.child:
            self._process_body_part(model, conn.part, plugin, sdf_part, conn.src, conn.dst)


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

    def get_sdf_model(self, robot, controller_plugin, name="sdf_robot"):
        """
        :param robot: Protobuf robot
        :type robot: Robot
        :param controller_plugin: Name of the shared library of the model plugin
        :type controller_plugin: str
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
        plugin.add_element(config)

        # Add brain config element
        brain_config = Element(tag_name='rv:brain')
        config.add_element(brain_config)

        self.brain_builder.build(robot, model, brain_config)
        self.body_builder.build(robot, model, config)

        model.add_element(plugin)
        return model
