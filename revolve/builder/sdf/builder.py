from math import radians

from sdfbuilder.base import Model

from ...spec import SpecImplementation, Robot, BodyPart as PbBodyPart, validate_robot
from ...spec.exception import err


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

    def get_sdf_model(self, robot, name="sdf_robot", validate=True):
        """
        :param robot: Protobuf robot
        :type robot: Robot
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
        self._process_body_part(model, robot.body.root)

        # TODO: Brain, motors, sensors

        return model

    def _process_body_part(self, model, part, parent=None, src_slot=None, dst_slot=None):
        """
        :param model:
        :type model: Model
        :param part:
        :type part: PbBodyPart
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

        # Process body connections
        for conn in part.child:
            self._process_body_part(model, conn.part, sdf_part, conn.src, conn.dst)