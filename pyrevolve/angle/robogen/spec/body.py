from __future__ import absolute_import

import random

from .. import Config
from ....revolve_bot.revolve_module import CoreModule, ActiveHingeModule, BrickModule, TouchSensorModule
from ....revolve_bot.body import FixedOrientationBodyGenerator
from ....spec import BodyImplementation, PartSpec, ParamSpec

# A utility function to generate color property parameters. Note that color
# parameters do not mutate.
channel_func = lambda channel: ParamSpec(
        channel,
        min_value=0,
        max_value=1,
        default=0.5,
        epsilon=0)
color_params = [
    channel_func("red"),
    channel_func("green"),
    channel_func("blue")
]


def get_body_spec(conf):
    """
    :return:
    :rtype: BodyImplementation
    """
    parts = {
        "Core": PartSpec(
            body_part=CoreModule,
            arity=4,
            inputs=0 if conf.disable_sensors else 6,
            params=color_params
        ),
        "FixedBrick": PartSpec(
            body_part=BrickModule,
            arity=4,
            params=color_params
        ),
        "ActiveHinge": PartSpec(
            body_part=ActiveHingeModule,
            arity=2,
            outputs=1,
            params=color_params
        ),

    }

    if not conf.disable_sensors:
        if conf.enable_touch_sensor:
            parts['TouchSensor'] = PartSpec(
                body_part=TouchSensorModule,
                arity=1,
                inputs=2,
                params=color_params
            )

    return BodyImplementation(parts)


class BodyGenerator(FixedOrientationBodyGenerator):
    """
    Body generator for ToL with some additions
    """

    def __init__(self, conf: Config):
        """
        """
        body_spec = get_body_spec(conf)
        self.conf = conf
        super(BodyGenerator, self).__init__(
            body_spec,

            # Only "Core" can serve as a root node
            root_parts=["Core"],

            # All other parts can potentially be attached
            attach_parts=[part_type for part_type in body_spec.get_all_types()
                          if part_type != "Core"],

            # Require at least some complexity
            min_parts=conf.min_parts,

            # High number of maximum parts, limit will probably be different
            max_parts=conf.max_parts,

            # Maximum number of sensory inputs
            max_inputs=conf.max_inputs,

            # Maximum number of motor outputs
            max_outputs=conf.max_outputs
        )
        self.last_parameters = None

    def initialize_part(
            self,
            spec,
            new_part,
            parent_part,
            root_part,
            root=False
    ):
        """
        Overrides `initialize_part` to make sure all parts get
        the same color as the root part
        :param parent_part:
        :param spec:
        :param new_part:
        :param root_part:
        :param root:
        """
        params = spec.get_random_parameters(serialize=False)
        if root:
            self.last_parameters = params
        elif self.last_parameters:
            params['red'], params['green'], params['blue'] = \
                self.last_parameters['red'],\
                self.last_parameters['green'],\
                self.last_parameters['blue']

        new_part.orientation = self.choose_orientation(
                new_part,
                parent_part,
                root_part,
                root)
        spec.set_parameters(new_part.param, params)
        return new_part

    def generate(self):
        """
        Resets `last_parameters` so that body parts built by the mutator
        will get random colors still.
        """
        result = super(BodyGenerator, self).generate()
        self.last_parameters = None
        return result

    def choose_part(self, parts, parent, body, root=False):
        """
        Overridable method to choose a body part from a list
        of part type identifiers.
        :param parts:
        :type parts: list[str]
        :param parent: Parent body part
        :param body: The robot body
        :param root: Whether the part is root
        :return: The chosen part
        :rtype: str
        """
        # Don't chain parametric bar joints, it leads to ugly constructions
        if parent and parent.type == "ParametricBarJoint":
            parts = [p for p in parts if p != "ParametricBarJoint"]

        return False if not parts else random.choice(parts)
