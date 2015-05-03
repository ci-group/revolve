from math import radians
from sdfbuilder.base import Model, Element
from ...spec import SpecImplementation, Robot, BodyPart as PbBodyPart, validate_robot
from ...spec.exception import err
from brain import Neuron, NeuralConnection


class Builder(object):
    """
    Constructor class to create an SDF model from a protobuf
    robot and a specification.
    """

    def __init__(self, spec, conf):
        """

        :param spec:
        :type spec: SpecImplementation
        :param conf:
        :return:
        """
        self.spec = spec
        self.conf = conf

    def get_sdf_model(self, robot, controller_plugin, name="sdf_robot", validate=True):
        """
        :param robot: Protobuf robot
        :type robot: Robot
        :param controller_plugin: Name of the shared library of the model plugin
        :type controller_plugin: str
        :param name: Name of the SDF model
        :type name: str
        :param validate: Whether or not to perform basic robot spec validation
        :type validate: bool
        :return: The sdfbuilder Model
        :rtype: Model
        """
        if validate:
            validate_robot(self.spec, robot)

        model = Model(name)

        # Create the model plugin element
        plugin = Element(tag_name='plugin', attributes={
            'name': 'robot_controller',
            'filename': controller_plugin
        })
        config = Element(tag_name='rv:robot_config', attributes={
            'xmlns:rv': 'https://github.com/ElteHupkes/revolve'
        })
        plugin.add_element(config)

        # Process the brain
        self._process_brain(plugin, robot.brain)

        # Process body parts recursively
        self._process_body_part(model, robot.body.root, config)
        model.add_element(plugin)

        return model

    def _process_brain(self, plugin, brain):
        """
        :param plugin:
        :type plugin: Element
        :param brain:
        :return:
        """
        # Add neurons
        for neuron in brain.neuron:
            spec = self.spec.get_neuron(neuron.type)
            if spec is None:
                err("Cannot build unknown neuron type '%s'." % neuron.type)

            params = spec.unserialize_params(neuron.param)
            plugin.add_element(Neuron(neuron, params))

        # Add connections
        for conn in brain.connection:
            plugin.add_element(NeuralConnection(conn))

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
        spec = self.spec.get_part(part.type)
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
            sdf_part.attach(model, parent, src_slot, dst_slot, radians(part.orientation))

        model.add_element(sdf_part)

        # Add sensors and motors
        plugin.add_elements(sdf_part.get_sensors())
        plugin.add_elements(sdf_part.get_motors())

        # Process body connections
        for conn in part.child:
            self._process_body_part(model, conn.part, plugin, sdf_part, conn.src, conn.dst)